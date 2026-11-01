from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date
from decimal import Decimal
import io

from households.models import Household
from meters.models import ElectricityMeter
from consumption.models import MeterReading
from consumption.services import import_readings_from_file
from core.reports import export_readings_csv, export_readings_excel


class ReportsAndImportsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reportuser", password="password123")
        self.household = Household.objects.create(
            created_by=self.user,
            name="Report Test House",
            sanctioned_load_kw=Decimal('3.00')
        )
        self.meter = ElectricityMeter.objects.create(
            household=self.household,
            meter_name="Main Digital Meter",
            meter_number="MTR-IMP-01",
            sanctioned_load_kw=Decimal('3.00')
        )
        MeterReading.objects.create(
            meter=self.meter,
            reading_date=date(2026, 1, 1),
            reading_value=Decimal('100.00'),
            consumption_kwh=Decimal('0.00'),
            reading_type='cumulative'
        )
        MeterReading.objects.create(
            meter=self.meter,
            reading_date=date(2026, 1, 2),
            reading_value=Decimal('112.50'),
            consumption_kwh=Decimal('12.50'),
            reading_type='cumulative'
        )

    def test_csv_export(self):
        """Verifies CSV export contains expected headers and formatted rows."""
        readings = MeterReading.objects.filter(meter=self.meter)
        res = export_readings_csv(readings, filename="test.csv")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'text/csv')
        content = res.content.decode('utf-8')
        self.assertIn("Meter Name,Meter Number,Reading Date", content)
        self.assertIn("112.50", content)

    def test_excel_export(self):
        """Verifies Excel workbook export response headers."""
        readings = MeterReading.objects.filter(meter=self.meter)
        res = export_readings_excel(readings, filename="test.xlsx")
        self.assertEqual(res.status_code, 200)
        self.assertIn("application/vnd.openxmlformats-officedocument", res['Content-Type'])

    def test_csv_import_valid_rows(self):
        """Verifies importing valid CSV readings into database."""
        csv_data = (
            "reading_date,reading_value,meter_number,reading_type,notes\n"
            "2026-01-03,125.00,MTR-IMP-01,cumulative,Day 3 reading\n"
            "2026-01-04,138.50,MTR-IMP-01,cumulative,Day 4 reading\n"
        )
        file_obj = io.BytesIO(csv_data.encode('utf-8'))
        file_obj.name = "import_test.csv"

        res = import_readings_from_file(
            file_obj=file_obj,
            household=self.household,
            meter_id=self.meter.id,
            user=self.user
        )

        self.assertTrue(res['success'])
        self.assertEqual(res['imported'], 2)
        self.assertEqual(res['failed'], 0)
        self.assertTrue(MeterReading.objects.filter(reading_date=date(2026, 1, 3)).exists())
        self.assertTrue(MeterReading.objects.filter(reading_date=date(2026, 1, 4)).exists())
