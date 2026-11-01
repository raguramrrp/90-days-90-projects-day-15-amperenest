from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date, timedelta
from decimal import Decimal

from households.models import Household
from meters.models import ElectricityMeter
from consumption.models import MeterReading
from billing.models import ElectricityBill
from alerts.models import EnergyAlertRule, EnergyAlert
from alerts.services import evaluate_household_alerts, initialize_default_rules
from tariffs.services import create_default_tamilnadu_tariff


class AlertsEngineTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alertsuser", password="password123")
        self.tariff = create_default_tamilnadu_tariff(user=self.user)
        self.household = Household.objects.create(
            created_by=self.user,
            name="Alerts Test House",
            monthly_budget_amount=Decimal('1000.00'),
            billing_cycle_day=1,
            sanctioned_load_kw=Decimal('3.00')
        )
        self.meter = ElectricityMeter.objects.create(
            household=self.household,
            meter_name="Alert Meter",
            meter_number="MTR-ALT-01",
            sanctioned_load_kw=Decimal('3.00'),
            tariff_plan=self.tariff
        )
        initialize_default_rules(self.household)

    def test_high_daily_consumption_trigger(self):
        """Reading exceeding threshold (e.g. 25 kWh > 15 kWh) generates a warning alert."""
        today = date.today()
        MeterReading.objects.create(
            meter=self.meter,
            reading_date=today,
            reading_value=Decimal('500.00'),
            consumption_kwh=Decimal('25.00'),
            reading_type='direct'
        )
        evaluate_household_alerts(self.household)
        alerts = EnergyAlert.objects.filter(household=self.household, alert_type='high_daily_kwh')
        self.assertTrue(alerts.exists())
        self.assertIn("High Daily Consumption", alerts.first().title)

    def test_bill_due_soon_trigger(self):
        """Unpaid bill due in 2 days should trigger a bill_due_soon alert."""
        today = date.today()
        ElectricityBill.objects.create(
            meter=self.meter,
            billing_period_start=today - timedelta(days=60),
            billing_period_end=today - timedelta(days=5),
            due_date=today + timedelta(days=2),
            total_units_kwh=Decimal('200.00'),
            total_bill_amount=Decimal('600.00'),
            payment_status='Pending'
        )
        evaluate_household_alerts(self.household)
        due_alerts = EnergyAlert.objects.filter(household=self.household, alert_type='bill_due_soon')
        self.assertTrue(due_alerts.exists())

    def test_inconsistent_reading_trigger(self):
        """Flagged inversion reading generates an inconsistent reading alert."""
        today = date.today()
        MeterReading.objects.create(
            meter=self.meter,
            reading_date=today,
            reading_value=Decimal('200.00'),
            is_flagged_inversion=True
        )
        evaluate_household_alerts(self.household)
        inv_alerts = EnergyAlert.objects.filter(household=self.household, alert_type='inconsistent_reading')
        self.assertTrue(inv_alerts.exists())
