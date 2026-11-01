from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date, timedelta
from decimal import Decimal
from django.db import IntegrityError

from households.models import Household
from meters.models import ElectricityMeter
from consumption.models import MeterReading


class MeterReadingsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.household = Household.objects.create(
            created_by=self.user,
            name="Test Household",
            sanctioned_load_kw=Decimal('3.00')
        )
        self.meter = ElectricityMeter.objects.create(
            household=self.household,
            meter_name="Main Meter",
            meter_number="MTR-001",
            sanctioned_load_kw=Decimal('3.00'),
            dial_digits=5
        )

    def test_first_reading_baseline(self):
        """First reading on a meter should establish baseline with 0 consumption."""
        r1 = MeterReading.objects.create(
            meter=self.meter,
            reading_date=date(2026, 1, 1),
            reading_value=Decimal('1000.00'),
            reading_type='cumulative'
        )
        self.assertEqual(r1.consumption_kwh, Decimal('0.00'))
        self.assertFalse(r1.is_flagged_inversion)

    def test_consecutive_reading_consumption_calculation(self):
        """Second reading should calculate consumption as the difference between dial values."""
        MeterReading.objects.create(
            meter=self.meter,
            reading_date=date(2026, 1, 1),
            reading_value=Decimal('1000.00'),
            reading_type='cumulative'
        )
        r2 = MeterReading.objects.create(
            meter=self.meter,
            reading_date=date(2026, 1, 2),
            reading_value=Decimal('1015.50'),
            reading_type='cumulative'
        )
        self.assertEqual(r2.consumption_kwh, Decimal('15.50'))
        self.assertFalse(r2.is_flagged_inversion)

    def test_decreasing_reading_inversion_flag(self):
        """A reading with lower dial value without reset flag must be flagged as an inversion."""
        MeterReading.objects.create(
            meter=self.meter,
            reading_date=date(2026, 1, 1),
            reading_value=Decimal('1000.00'),
            reading_type='cumulative'
        )
        r2 = MeterReading.objects.create(
            meter=self.meter,
            reading_date=date(2026, 1, 2),
            reading_value=Decimal('950.00'),
            reading_type='cumulative'
        )
        self.assertTrue(r2.is_flagged_inversion)
        self.assertEqual(r2.consumption_kwh, Decimal('0.00'))

    def test_meter_rollover_reset_calculation(self):
        """When flagged as reset/rollover, consumption should compute across the dial limit."""
        MeterReading.objects.create(
            meter=self.meter,
            reading_date=date(2026, 1, 1),
            reading_value=Decimal('99990.00'),
            reading_type='cumulative'
        )
        # Dial rolled over from 99990 -> 100000 -> 15.00 (99990 to 100000 is 10, plus 15 = 25)
        r2 = MeterReading.objects.create(
            meter=self.meter,
            reading_date=date(2026, 1, 2),
            reading_value=Decimal('15.00'),
            reading_type='cumulative',
            is_meter_reset_or_replacement=True
        )
        self.assertFalse(r2.is_flagged_inversion)
        self.assertEqual(r2.consumption_kwh, Decimal('25.00'))

    def test_direct_consumption_entry(self):
        """Direct consumption entries should record specified units directly."""
        r = MeterReading.objects.create(
            meter=self.meter,
            reading_date=date(2026, 1, 3),
            reading_value=Decimal('12.50'),
            consumption_kwh=Decimal('12.50'),
            reading_type='direct'
        )
        self.assertEqual(r.consumption_kwh, Decimal('12.50'))
        self.assertEqual(r.reading_type, 'direct')

    def test_duplicate_reading_date_rejected(self):
        """Database constraint should prevent duplicate readings for the same meter on the same date."""
        MeterReading.objects.create(
            meter=self.meter,
            reading_date=date(2026, 1, 1),
            reading_value=Decimal('1000.00')
        )
        with self.assertRaises(IntegrityError):
            MeterReading.objects.create(
                meter=self.meter,
                reading_date=date(2026, 1, 1),
                reading_value=Decimal('1010.00')
            )
