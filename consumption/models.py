from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal


class MeterReading(models.Model):
    READING_TYPES = [
        ('cumulative', 'Cumulative Meter Reading (Dial Value)'),
        ('direct', 'Direct Consumption (kWh used in period)'),
    ]

    SOURCES = [
        ('Manual Entry', 'Manual Entry (User Recorded)'),
        ('CSV/Excel Import', 'CSV / Excel Import'),
        ('Smart Meter', 'Smart Meter Automated Sync'),
        ('Estimated', 'System Estimated Reading'),
    ]

    meter = models.ForeignKey('meters.ElectricityMeter', on_delete=models.CASCADE, related_name='readings')
    reading_date = models.DateField(help_text="Date the reading was taken")
    reading_time = models.TimeField(null=True, blank=True)
    reading_value = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Meter display reading in kWh"
    )
    consumption_kwh = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text="Calculated or entered electricity consumed in kWh for this interval"
    )
    reading_type = models.CharField(max_length=20, choices=READING_TYPES, default='cumulative')
    reading_source = models.CharField(max_length=30, choices=SOURCES, default='Manual Entry')

    is_flagged_inversion = models.BooleanField(
        default=False,
        help_text="True if this cumulative reading is lower than the previous reading without reset flag"
    )
    is_meter_reset_or_replacement = models.BooleanField(
        default=False,
        help_text="Check if the meter was replaced, rolled over, or reset by the utility"
    )
    supporting_image = models.ImageField(upload_to='meter_readings/', blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-reading_date', '-id']
        unique_together = ('meter', 'reading_date')

    def __str__(self):
        return f"{self.meter.meter_name} - {self.reading_date}: {self.reading_value} kWh (+{self.consumption_kwh} kWh)"

    def clean(self):
        super().clean()
        if self.reading_type == 'cumulative' and self.meter_id:
            # Check previous reading
            prev = MeterReading.objects.filter(
                meter=self.meter,
                reading_date__lt=self.reading_date
            ).exclude(pk=self.pk).order_by('-reading_date').first()

            if prev:
                if self.reading_value < prev.reading_value and not self.is_meter_reset_or_replacement:
                    self.is_flagged_inversion = True
                else:
                    self.is_flagged_inversion = False

    def save(self, *args, **kwargs):
        # Auto-compute consumption_kwh if cumulative reading and not manually specified
        if self.reading_type == 'cumulative':
            prev = MeterReading.objects.filter(
                meter=self.meter,
                reading_date__lt=self.reading_date
            ).exclude(pk=self.pk).order_by('-reading_date').first()

            if prev:
                if self.reading_value >= prev.reading_value:
                    self.consumption_kwh = self.reading_value - prev.reading_value
                elif self.is_meter_reset_or_replacement:
                    # Rollover calculation based on meter dial digits (e.g. 100,000 max)
                    max_dial = Decimal(10 ** self.meter.dial_digits)
                    self.consumption_kwh = (max_dial - prev.reading_value) + self.reading_value
                else:
                    self.is_flagged_inversion = True
                    self.consumption_kwh = Decimal('0.00')
            else:
                # First reading on this meter establishes baseline
                self.consumption_kwh = Decimal('0.00')

        super().save(*args, **kwargs)

        # Re-evaluate next reading if it exists, to keep its consumption_kwh accurate
        next_reading = MeterReading.objects.filter(
            meter=self.meter,
            reading_date__gt=self.reading_date
        ).order_by('reading_date').first()

        if next_reading and next_reading.reading_type == 'cumulative':
            if next_reading.reading_value >= self.reading_value:
                new_cons = next_reading.reading_value - self.reading_value
                if next_reading.consumption_kwh != new_cons or next_reading.is_flagged_inversion:
                    next_reading.consumption_kwh = new_cons
                    next_reading.is_flagged_inversion = False
                    MeterReading.objects.filter(pk=next_reading.pk).update(
                        consumption_kwh=new_cons,
                        is_flagged_inversion=False
                    )


class ImportHistory(models.Model):
    household = models.ForeignKey('households.Household', on_delete=models.CASCADE, related_name='import_history')
    meter = models.ForeignKey('meters.ElectricityMeter', on_delete=models.SET_NULL, null=True, blank=True)
    file_name = models.CharField(max_length=200)
    imported_at = models.DateTimeField(auto_now_add=True)
    rows_processed = models.PositiveIntegerField(default=0)
    rows_imported = models.PositiveIntegerField(default=0)
    rows_failed = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default='Success')
    error_summary = models.TextField(blank=True)
    imported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-imported_at']

    def __str__(self):
        return f"Import {self.file_name} ({self.status}) - {self.imported_at.strftime('%Y-%m-%d %H:%M')}"
