from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class ElectricityMeter(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active Meter'),
        ('Archived', 'Archived / Replaced'),
        ('Under Maintenance', 'Under Maintenance / Inspection'),
    ]

    CONNECTION_TYPES = [
        ('1_phase', 'Single Phase (230V, Up to 4 kW)'),
        ('3_phase', 'Three Phase (415V, 5 kW and above)'),
    ]

    CONSUMER_CATEGORIES = [
        ('residential_domestic', 'Residential (Domestic LT-1A)'),
        ('commercial', 'Commercial / Small Business (LT-3)'),
        ('agricultural', 'Agricultural / Farm Pump'),
        ('temporary', 'Temporary Construction Supply'),
    ]

    BILLING_CYCLES = [
        ('Bimonthly', 'Bimonthly (Every 2 Months / TN Standard)'),
        ('Monthly', 'Monthly (Every Month)'),
        ('Quarterly', 'Quarterly (Every 3 Months)'),
    ]

    household = models.ForeignKey('households.Household', on_delete=models.CASCADE, related_name='meters')
    meter_name = models.CharField(max_length=120, help_text="e.g. Main Digital Meter, 1st Floor Sub-meter")
    meter_number = models.CharField(max_length=80, help_text="Physical serial number printed on the meter")
    service_number = models.CharField(max_length=80, blank=True, help_text="Utility consumer connection / account number")
    electricity_provider = models.CharField(max_length=100, default='TANGEDCO / TNPDCL')
    consumer_category = models.CharField(max_length=40, choices=CONSUMER_CATEGORIES, default='residential_domestic')
    connection_type = models.CharField(max_length=20, choices=CONNECTION_TYPES, default='1_phase')
    sanctioned_load_kw = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('3.00'),
        validators=[MinValueValidator(0.1)],
        help_text="Sanctioned connected load in kW"
    )
    installation_date = models.DateField(null=True, blank=True)
    reading_unit = models.CharField(max_length=10, default='kWh')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES, default='Bimonthly')
    tariff_plan = models.ForeignKey(
        'tariffs.TariffPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_meters',
        help_text="Tariff structure applied to calculate bills for this meter"
    )
    meter_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    dial_digits = models.PositiveIntegerField(default=5, help_text="Number of whole digits on meter display before rollover (e.g. 5 digits = 99,999)")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['meter_status', 'meter_name']
        unique_together = ('household', 'meter_number')

    def __str__(self):
        return f"{self.meter_name} ({self.meter_number}) - {self.household.name}"

    @property
    def latest_reading(self):
        return self.readings.order_by('-reading_date', '-id').first()

    @property
    def total_readings_count(self):
        return self.readings.count()
