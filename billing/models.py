from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class ElectricityBill(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending Payment'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue'),
    ]

    meter = models.ForeignKey('meters.ElectricityMeter', on_delete=models.CASCADE, related_name='bills')
    tariff_plan = models.ForeignKey('tariffs.TariffPlan', on_delete=models.SET_NULL, null=True, blank=True)
    bill_number = models.CharField(max_length=80, blank=True, help_text="Utility bill / reference invoice number")
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    issue_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    previous_reading = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    current_reading = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_units_kwh = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])

    energy_charges = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    fixed_charges = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    duty_and_taxes = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    subsidies_and_adjustments = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_bill_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])

    is_estimated_bill = models.BooleanField(
        default=False,
        help_text="True if this is a forecast or simulated estimate rather than an official utility bill"
    )
    actual_bill_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Official bill amount entered to compare with simulation"
    )

    bill_document = models.FileField(upload_to='bills/', blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-billing_period_end', '-id']

    def __str__(self):
        bill_type = "Estimated" if self.is_estimated_bill else "Actual"
        return f"{self.meter.meter_name} ({self.billing_period_start} to {self.billing_period_end}) - ₹{self.total_bill_amount} [{bill_type}]"

    def update_payment_status(self):
        """Automatically synchronizes payment status based on dates."""
        today = timezone.localdate()
        if self.payment_date:
            self.payment_status = 'Paid'
        elif self.due_date and self.due_date < today:
            self.payment_status = 'Overdue'
        else:
            self.payment_status = 'Pending'

    def save(self, *args, **kwargs):
        self.update_payment_status()
        super().save(*args, **kwargs)

    @property
    def variance_amount(self):
        if self.actual_bill_amount is not None:
            return (self.actual_bill_amount - self.total_bill_amount).quantize(Decimal('0.01'))
        return None

    @property
    def variance_percentage(self):
        if self.actual_bill_amount is not None and self.total_bill_amount > 0:
            diff = self.actual_bill_amount - self.total_bill_amount
            return ((diff / self.total_bill_amount) * Decimal('100.0')).quantize(Decimal('0.1'))
        return None


class BillLineItem(models.Model):
    ITEM_TYPES = [
        ('energy_slab', 'Energy Charge (Slab)'),
        ('fixed_charge', 'Fixed Connected Load Charge'),
        ('duty_tax', 'Electricity Duty / Tax'),
        ('surcharge', 'Surcharge / FPPCA Fuel Cost'),
        ('subsidy', 'Govt Subsidy / Concession'),
        ('adjustment', 'Adjustment / Meter Rent'),
    ]

    bill = models.ForeignKey(ElectricityBill, on_delete=models.CASCADE, related_name='line_items')
    item_type = models.CharField(max_length=30, choices=ITEM_TYPES, default='energy_slab')
    description = models.CharField(max_length=200)
    units_applicable = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.description}: ₹{self.amount}"
