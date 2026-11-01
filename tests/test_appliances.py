from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal

from households.models import Household
from appliances.models import Appliance


class ApplianceIntelligenceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="applianceuser", password="password123")
        self.household = Household.objects.create(
            created_by=self.user,
            name="Smart House",
            sanctioned_load_kw=Decimal('5.00')
        )
        # AC: 1500W, 6.0 hrs/day, 30 days/month
        self.ac = Appliance.objects.create(
            household=self.household,
            name="Master Inverter AC",
            category="air_conditioner",
            rated_power_watts=1500,
            quantity=1,
            daily_operating_hours=Decimal('6.00'),
            days_used_per_month=30,
            standby_power_watts=Decimal('0.00'),
            is_active=True
        )

    def test_daily_consumption_calculation(self):
        """1500W * 6 hours = 9.0 kWh daily."""
        self.assertEqual(self.ac.daily_consumption_kwh, Decimal('9.00'))

    def test_monthly_consumption_calculation(self):
        """9.0 kWh/day * 30 days = 270.0 kWh monthly."""
        self.assertEqual(self.ac.monthly_consumption_kwh, Decimal('270.00'))

    def test_monthly_cost_estimate(self):
        """270 kWh * ₹5.50 = ₹1,485.00."""
        self.assertEqual(self.ac.estimate_monthly_cost(rate_per_kwh=Decimal('5.50')), Decimal('1485.00'))

    def test_savings_simulator(self):
        """Simulate reducing AC daily runtime from 6.0 to 4.0 hours."""
        # 4.0h daily -> 6.0 kWh/d * 30d = 180 kWh
        # Saved: 270 - 180 = 90 kWh
        # Cost saved: 90 * 5.50 = ₹495.00
        sim = self.ac.simulate_savings(proposed_hours=Decimal('4.00'), rate_per_kwh=Decimal('5.50'))
        self.assertEqual(sim['kwh_saved'], Decimal('90.00'))
        self.assertEqual(sim['cost_saved'], Decimal('495.00'))
