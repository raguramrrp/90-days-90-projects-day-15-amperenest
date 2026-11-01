from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date, timedelta
from decimal import Decimal

from households.models import Household
from meters.models import ElectricityMeter
from consumption.models import MeterReading
from tariffs.services import create_default_tamilnadu_tariff
from analytics.services import generate_billing_cycle_forecast, generate_energy_insights, get_dashboard_chart_data


class AnalyticsAndForecastingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="analyticsuser", password="password123")
        self.tariff = create_default_tamilnadu_tariff(user=self.user)
        self.household = Household.objects.create(
            created_by=self.user,
            name="Green Habitat",
            billing_cycle_day=1,
            monthly_budget_amount=Decimal('2000.00'),
            sanctioned_load_kw=Decimal('3.00')
        )
        self.meter = ElectricityMeter.objects.create(
            household=self.household,
            meter_name="Main Meter",
            meter_number="MTR-AN-01",
            sanctioned_load_kw=Decimal('3.00'),
            tariff_plan=self.tariff
        )

    def test_forecast_safeguard_with_insufficient_data(self):
        """When fewer than 2 readings exist, forecast honestly refuses to fabricate predictions."""
        # Only 1 reading exists
        MeterReading.objects.create(
            meter=self.meter,
            reading_date=date.today(),
            reading_value=Decimal('100.00')
        )
        forecast = generate_billing_cycle_forecast(self.household)
        self.assertFalse(forecast['has_sufficient_data'])
        self.assertIn("Insufficient readings", forecast['message'])
        self.assertIsNone(forecast['projected_total_kwh'])

    def test_forecast_projection_with_sufficient_data(self):
        """With daily readings present, projects linear moving average to end of cycle."""
        today = date.today()
        # Add 10 consecutive daily readings
        cur_dial = Decimal('1000.00')
        for i in range(10, 0, -1):
            cur_dial += Decimal('10.00') # 10 kWh daily
            MeterReading.objects.create(
                meter=self.meter,
                reading_date=today - timedelta(days=i),
                reading_value=cur_dial,
                consumption_kwh=Decimal('10.00')
            )

        forecast = generate_billing_cycle_forecast(self.household)
        self.assertTrue(forecast['has_sufficient_data'])
        self.assertGreater(forecast['projected_total_kwh'], Decimal('0.00'))
        self.assertGreater(forecast['confidence_score_pct'], Decimal('50.0'))

    def test_dashboard_chart_data_structure(self):
        """Verifies chart data dictionary contains expected array structures."""
        chart_data = get_dashboard_chart_data(self.household)
        self.assertIn('daily_dates', chart_data)
        self.assertIn('daily_kwh', chart_data)
        self.assertIn('monthly_labels', chart_data)
        self.assertIn('monthly_kwh', chart_data)
        self.assertEqual(len(chart_data['daily_dates']), 30)
