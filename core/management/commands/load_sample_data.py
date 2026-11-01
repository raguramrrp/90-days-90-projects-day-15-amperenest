from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import random

from accounts.models import UserProfile
from households.models import Household, HouseholdMember
from meters.models import ElectricityMeter
from tariffs.models import TariffPlan, TariffSlab, TariffCharge
from tariffs.services import create_default_tamilnadu_tariff
from consumption.models import MeterReading
from billing.models import ElectricityBill, BillLineItem
from appliances.models import Appliance
from budgets.models import EnergyBudget, EnergyGoal
from alerts.models import EnergyAlertRule, EnergyAlert
from alerts.services import initialize_default_rules, evaluate_household_alerts
from analytics.models import ForecastRecord, SavingsScenario


class Command(BaseCommand):
    help = "Loads realistic sample data for AmpereNest household electricity management"

    def handle(self, *args, **options):
        self.stdout.write("Initializing sample data for AmpereNest...")

        # 1. Create or get demo user
        demo_user, created = User.objects.get_or_create(
            username="demouser",
            defaults={
                'email': 'demo@amperenest.local',
                'first_name': 'Ragu',
                'last_name': 'Ram'
            }
        )
        if created:
            demo_user.set_password("demo1234")
            demo_user.save()
            self.stdout.write(self.style.SUCCESS(f"Created demo user: demouser (password: demo1234)"))

        profile, _ = UserProfile.objects.get_or_create(user=demo_user)
        profile.phone_number = "+91 98765 43210"
        profile.theme_preference = "light"
        profile.currency_symbol = "₹"
        profile.save()

        # 2. Tariff Plan
        tariff = create_default_tamilnadu_tariff(user=demo_user)
        self.stdout.write(self.style.SUCCESS(f"Configured Tariff: {tariff.name}"))

        # 3. Create Households
        h1, _ = Household.objects.get_or_create(
            created_by=demo_user,
            name="Anna Nagar Residence",
            defaults={
                'property_type': 'independent_house',
                'address_line1': 'Plot 42, 2nd Avenue, Anna Nagar East',
                'city': 'Chennai',
                'state': 'Tamil Nadu',
                'postal_code': '600102',
                'country': 'India',
                'occupants': 4,
                'sanctioned_load_kw': Decimal('5.00'),
                'monthly_budget_amount': Decimal('2200.00'),
                'billing_cycle_day': 1,
            }
        )

        h2, _ = Household.objects.get_or_create(
            created_by=demo_user,
            name="Madurai Family Villa",
            defaults={
                'property_type': 'villa',
                'address_line1': '15 Bypass Road, Ponmeni',
                'city': 'Madurai',
                'state': 'Tamil Nadu',
                'postal_code': '625016',
                'country': 'India',
                'occupants': 5,
                'sanctioned_load_kw': Decimal('7.50'),
                'monthly_budget_amount': Decimal('3800.00'),
                'billing_cycle_day': 15,
            }
        )

        profile.default_household = h1
        profile.save()

        # 4. Meters for Household 1
        m1, _ = ElectricityMeter.objects.get_or_create(
            household=h1,
            meter_number="04-201-008-1422",
            defaults={
                'meter_name': 'Main Residential Digital Meter',
                'service_number': '042010081422',
                'electricity_provider': 'TANGEDCO / TNPDCL',
                'consumer_category': 'residential_domestic',
                'connection_type': '3_phase',
                'sanctioned_load_kw': Decimal('5.00'),
                'installation_date': date(2022, 4, 15),
                'reading_unit': 'kWh',
                'billing_cycle': 'Bimonthly',
                'tariff_plan': tariff,
                'meter_status': 'Active',
                'dial_digits': 5,
                'notes': 'Three-phase electronic static meter on ground floor distribution board.'
            }
        )

        m2, _ = ElectricityMeter.objects.get_or_create(
            household=h1,
            meter_number="04-201-008-1423",
            defaults={
                'meter_name': 'Submersible Borewell & Utility Meter',
                'service_number': '042010081423',
                'electricity_provider': 'TANGEDCO / TNPDCL',
                'consumer_category': 'residential_domestic',
                'connection_type': '1_phase',
                'sanctioned_load_kw': Decimal('2.00'),
                'installation_date': date(2023, 1, 10),
                'reading_unit': 'kWh',
                'billing_cycle': 'Bimonthly',
                'tariff_plan': tariff,
                'meter_status': 'Active',
                'dial_digits': 5,
                'notes': 'Dedicated line for garden irrigation pump and terrace overhead storage pump.'
            }
        )

        # 5. Populate realistic historical readings for m1 (past 90 days)
        today = timezone.localdate()
        random.seed(42)

        # Clear existing readings for a clean baseline if needed
        if m1.readings.count() < 30:
            current_dial = Decimal('14250.00')
            start_date = today - timedelta(days=90)
            cur_date = start_date

            while cur_date <= today:
                # Seasonal variation: hotter days = 10-16 kWh, cooler days = 6-10 kWh
                month = cur_date.month
                if month in (4, 5, 6, 7): # Summer
                    daily_units = Decimal(str(round(random.uniform(11.0, 16.5), 2)))
                else:
                    daily_units = Decimal(str(round(random.uniform(6.5, 11.0), 2)))

                # Weekend slight increase
                if cur_date.weekday() >= 5:
                    daily_units += Decimal('2.50')

                current_dial += daily_units

                MeterReading.objects.update_or_create(
                    meter=m1,
                    reading_date=cur_date,
                    defaults={
                        'reading_value': current_dial,
                        'consumption_kwh': daily_units,
                        'reading_type': 'cumulative',
                        'reading_source': 'Manual Entry',
                        'recorded_by': demo_user
                    }
                )
                cur_date += timedelta(days=1)
            self.stdout.write(self.style.SUCCESS(f"Created 90 daily readings for {m1.meter_name}"))

        # 6. Populate readings for m2 (pumps run every 2-3 days)
        if m2.readings.count() < 15:
            current_dial_m2 = Decimal('2480.00')
            cur_date = today - timedelta(days=90)
            while cur_date <= today:
                if cur_date.day % 2 == 0:
                    pump_units = Decimal(str(round(random.uniform(1.2, 2.5), 2)))
                    current_dial_m2 += pump_units
                    MeterReading.objects.update_or_create(
                        meter=m2,
                        reading_date=cur_date,
                        defaults={
                            'reading_value': current_dial_m2,
                            'consumption_kwh': pump_units,
                            'reading_type': 'cumulative',
                            'reading_source': 'Manual Entry',
                            'recorded_by': demo_user
                        }
                    )
                cur_date += timedelta(days=1)

        # 7. Create Historical Electricity Bills for m1
        bill_periods = [
            (today - timedelta(days=120), today - timedelta(days=61), Decimal('520.00'), 'Paid', today - timedelta(days=45)),
            (today - timedelta(days=60), today - timedelta(days=1), Decimal('480.00'), 'Pending', None),
        ]

        for p_start, p_end, units, status, paid_date in bill_periods:
            bill_calc = tariff.calculate_bill(units, m1.sanctioned_load_kw)
            bill_num = f"TNEB-{p_start.strftime('%Y%m')}-{random.randint(1000, 9999)}"

            due = p_end + timedelta(days=20)

            bill, b_created = ElectricityBill.objects.update_or_create(
                meter=m1,
                billing_period_start=p_start,
                billing_period_end=p_end,
                defaults={
                    'tariff_plan': tariff,
                    'bill_number': bill_num,
                    'issue_date': p_end + timedelta(days=2),
                    'due_date': due,
                    'payment_date': paid_date,
                    'payment_status': status,
                    'total_units_kwh': units,
                    'energy_charges': bill_calc['net_energy_charges'],
                    'fixed_charges': bill_calc['fixed_charges'],
                    'duty_and_taxes': bill_calc['electricity_duty_amount'],
                    'subsidies_and_adjustments': bill_calc['subsidy_amount'],
                    'total_bill_amount': bill_calc['total_bill_amount'],
                    'actual_bill_amount': bill_calc['total_bill_amount'] if status == 'Paid' else None,
                    'is_estimated_bill': False,
                    'notes': f"Bimonthly official domestic electricity statement for {p_start.strftime('%b')} - {p_end.strftime('%b %Y')}."
                }
            )

            if b_created:
                # Add line items
                for s in bill_calc['slab_breakdown']:
                    BillLineItem.objects.create(
                        bill=bill,
                        item_type='energy_slab',
                        description=f"Energy Charge: Slab ({s['range']})",
                        units_applicable=s['units'],
                        rate=s['rate'],
                        amount=s['amount']
                    )
                if bill_calc['subsidy_amount'] > 0:
                    BillLineItem.objects.create(
                        bill=bill,
                        item_type='subsidy',
                        description=tariff.subsidy_description,
                        units_applicable=Decimal(str(tariff.free_units_per_cycle)),
                        rate=Decimal('4.50'),
                        amount=-bill_calc['subsidy_amount']
                    )
                if bill_calc['electricity_duty_amount'] > 0:
                    BillLineItem.objects.create(
                        bill=bill,
                        item_type='duty_tax',
                        description=f"Tamil Nadu Electricity Tax ({tariff.electricity_duty_pct}%)",
                        amount=bill_calc['electricity_duty_amount']
                    )

        # 8. Create Realistic Appliance Inventory
        appliances_data = [
            ("Master Bedroom Inverter Split AC 1.5T", "air_conditioner", "Daikin", 1450, 1, Decimal('6.00'), 30, Decimal('3.50'), 5),
            ("Kids Bedroom 3-Star Split AC 1.0T", "air_conditioner", "Voltas", 1100, 1, Decimal('4.00'), 25, Decimal('3.00'), 3),
            ("Double Door Frost-Free Refrigerator 340L", "refrigerator", "LG", 160, 1, Decimal('10.00'), 30, Decimal('0.00'), 4),
            ("Living Room & Dining BLDC Ceiling Fans", "ceiling_fan", "Atomberg", 28, 3, Decimal('12.00'), 30, Decimal('0.50'), 5),
            ("Bedroom Conventional Ceiling Fans", "ceiling_fan", "Crompton", 75, 2, Decimal('8.00'), 30, Decimal('0.00'), 2),
            ("Borewell Submersible Water Pump 1 HP", "water_pump", "Texmo", 750, 1, Decimal('1.25'), 30, Decimal('0.00'), 3),
            ("Bathroom Storage Geyser 25L", "water_heater", "AO Smith", 2000, 1, Decimal('1.00'), 30, Decimal('0.00'), 4),
            ("Smart LED 4K Television 55 Inch", "television", "Sony", 110, 1, Decimal('4.50'), 30, Decimal('1.50'), 4),
            ("Fully Automatic Front Load Washing Machine", "washing_machine", "Bosch", 1800, 1, Decimal('0.75'), 15, Decimal('1.00'), 5),
            ("Workstation PC & Monitor", "computer_laptop", "Dell", 180, 1, Decimal('8.00'), 26, Decimal('4.00'), 4),
            ("Home LED Lighting Circuit (Whole House)", "lighting", "Philips", 120, 1, Decimal('6.00'), 30, Decimal('0.00'), 5),
            ("Convection Microwave Oven 28L", "microwave", "Samsung", 1200, 1, Decimal('0.30'), 20, Decimal('2.00'), 3),
        ]

        for name, cat, brand, watts, qty, hrs, days, standby, stars in appliances_data:
            Appliance.objects.update_or_create(
                household=h1,
                name=name,
                defaults={
                    'category': cat,
                    'brand': brand,
                    'rated_power_watts': watts,
                    'quantity': qty,
                    'daily_operating_hours': hrs,
                    'days_used_per_month': days,
                    'standby_power_watts': standby,
                    'energy_star_rating': stars,
                    'is_active': True,
                    'notes': f"Household energy audit item: {brand} {stars}-star {cat.replace('_', ' ').title()}."
                }
            )

        self.stdout.write(self.style.SUCCESS(f"Loaded {len(appliances_data)} appliances into inventory"))

        # 9. Energy Budgets & Goals
        EnergyBudget.objects.update_or_create(
            household=h1,
            month=today.month,
            year=today.year,
            defaults={
                'monthly_budget_amount': Decimal('2200.00'),
                'target_consumption_kwh': Decimal('280.00'),
                'daily_target_kwh': Decimal('9.30'),
                'notes': f"Target for {today.strftime('%B %Y')}: keep daily consumption under 9.5 kWh."
            }
        )

        EnergyGoal.objects.update_or_create(
            household=h1,
            title="Limit Summer Air Conditioner Usage to 5 hrs/day",
            defaults={
                'goal_type': 'appliance_reduction',
                'target_value': Decimal('5.00'),
                'current_value': Decimal('6.00'),
                'unit': 'Hours/day',
                'start_date': today - timedelta(days=15),
                'target_date': today + timedelta(days=30),
                'status': 'In Progress',
                'notes': 'Setting AC thermostat to 24°C and timer to shut off at 4 AM.'
            }
        )

        EnergyGoal.objects.update_or_create(
            household=h1,
            title="Keep Bimonthly Electricity Bill Under ₹2,000",
            defaults={
                'goal_type': 'budget_limit',
                'target_value': Decimal('2000.00'),
                'current_value': Decimal('1650.00'),
                'unit': '₹',
                'start_date': today - timedelta(days=30),
                'target_date': today + timedelta(days=30),
                'status': 'In Progress',
                'notes': 'Maintain monthly average under 150 kWh to benefit from TN 100 free units subsidy.'
            }
        )

        # 10. Savings Scenarios
        ac_appliance = h1.appliances.filter(category='air_conditioner').first()
        if ac_appliance:
            SavingsScenario.objects.update_or_create(
                household=h1,
                name="Reduce Master Bedroom AC by 1.5 Hours Daily",
                defaults={
                    'appliance': ac_appliance,
                    'proposed_daily_hours': Decimal('4.50'),
                    'proposed_power_watts': 1450,
                    'monthly_kwh_saved': Decimal('65.25'),
                    'monthly_cost_saved': Decimal('391.50'),
                    'notes': "Hypothetical scenario based on running bedroom AC from 11 PM to 3:30 AM with ceiling fan."
                }
            )

        # 11. Initialize alert rules & evaluate alerts
        initialize_default_rules(h1)
        evaluate_household_alerts(h1)

        self.stdout.write(self.style.SUCCESS("Sample data successfully created and loaded into AmpereNest!"))
