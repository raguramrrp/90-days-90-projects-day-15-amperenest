from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date
from decimal import Decimal

from tariffs.models import TariffPlan, TariffSlab, TariffCharge
from tariffs.services import create_default_tamilnadu_tariff, get_tariff_for_date
from households.models import Household
from meters.models import ElectricityMeter
from billing.models import ElectricityBill


class TariffsAndBillingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tariffuser", password="password123")
        self.tariff = create_default_tamilnadu_tariff(user=self.user)
        self.household = Household.objects.create(
            created_by=self.user,
            name="Chennai Villa",
            sanctioned_load_kw=Decimal('5.00')
        )
        self.meter = ElectricityMeter.objects.create(
            household=self.household,
            meter_name="Main 3-Phase",
            meter_number="MTR-TN-01",
            sanctioned_load_kw=Decimal('5.00'),
            tariff_plan=self.tariff
        )

    def test_tamil_nadu_tariff_structure_integrity(self):
        """Verifies Tamil Nadu Domestic LT-1A slabs and free units subsidy configuration."""
        self.assertEqual(self.tariff.slabs.count(), 5)
        self.assertEqual(self.tariff.free_units_per_cycle, 100)
        self.assertEqual(self.tariff.electricity_duty_pct, Decimal('5.00'))

    def test_bill_calculation_under_100_units(self):
        """Consumption under 100 units should benefit fully from 100 free units subsidy."""
        calc = self.tariff.calculate_bill(units_consumed=80, sanctioned_load_kw=Decimal('5.0'))
        # 80 units * ₹4.50 = ₹360 gross, minus ₹360 subsidy = ₹0 net energy
        self.assertEqual(calc['gross_energy_charges'], Decimal('360.00'))
        self.assertEqual(calc['subsidy_amount'], Decimal('360.00'))
        self.assertEqual(calc['net_energy_charges'], Decimal('0.00'))
        # FPPCA: 80 * 0.25 = ₹20.00
        self.assertEqual(calc['total_bill_amount'], Decimal('20.00'))

    def test_bill_calculation_250_units(self):
        """Consumption of 250 units across telescopic slabs."""
        # Slabs:
        # 0-100: 100 * 4.50 = 450
        # 100-200: 100 * 4.50 = 450
        # 200-250: 50 * 6.00 = 300
        # Gross = 1200
        # Subsidy = 100 units * 4.50 = 450
        # Net energy = 1200 - 450 = 750
        # Duty 5% of 750 = 37.50
        # FPPCA: 250 * 0.25 = 62.50
        # Total = 750 + 37.50 + 62.50 = 850.00
        calc = self.tariff.calculate_bill(units_consumed=250, sanctioned_load_kw=Decimal('5.0'))
        self.assertEqual(calc['gross_energy_charges'], Decimal('1200.00'))
        self.assertEqual(calc['subsidy_amount'], Decimal('450.00'))
        self.assertEqual(calc['net_energy_charges'], Decimal('750.00'))
        self.assertEqual(calc['electricity_duty_amount'], Decimal('37.50'))
        self.assertEqual(calc['total_bill_amount'], Decimal('850.00'))

    def test_historical_tariff_date_lookup(self):
        """get_tariff_for_date should retrieve the tariff effective on the given date."""
        resolved = get_tariff_for_date(self.meter, target_date=date(2025, 1, 1))
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.id, self.tariff.id)

    def test_bill_variance_calculation(self):
        """ElectricityBill should compute difference and percentage between actual and estimated bill."""
        bill = ElectricityBill.objects.create(
            meter=self.meter,
            tariff_plan=self.tariff,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 2, 28),
            total_units_kwh=Decimal('250.00'),
            total_bill_amount=Decimal('850.00'),
            actual_bill_amount=Decimal('880.00')
        )
        self.assertEqual(bill.variance_amount, Decimal('30.00'))
        self.assertAlmostEqual(float(bill.variance_percentage), 3.5, delta=0.2)
