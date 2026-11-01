from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal, ROUND_HALF_UP


class TariffPlan(models.Model):
    FREQUENCY_CHOICES = [
        ('Monthly', 'Monthly (30 Days)'),
        ('Bimonthly', 'Bimonthly (60 Days / Tamil Nadu Standard)'),
        ('Quarterly', 'Quarterly (90 Days)'),
    ]

    FIXED_CHARGE_TYPES = [
        ('flat_per_cycle', 'Flat Fixed Charge per Billing Cycle (₹)'),
        ('per_kw_sanctioned', 'Per kW Sanctioned Load per Cycle (₹/kW)'),
        ('none', 'No Fixed Charges'),
    ]

    name = models.CharField(max_length=150, help_text="e.g. TANGEDCO Domestic LT-1A (2024-2025)")
    provider = models.CharField(max_length=100, default='TANGEDCO / TNPDCL')
    state = models.CharField(max_length=100, default='Tamil Nadu')
    country = models.CharField(max_length=60, default='India')
    consumer_category = models.CharField(max_length=100, default='Residential (Domestic LT-1A)')
    billing_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='Bimonthly')

    effective_from = models.DateField(help_text="Date from which this tariff schedule applies")
    effective_to = models.DateField(null=True, blank=True, help_text="Leave blank if currently active")
    is_active = models.BooleanField(default=True)

    fixed_charge_type = models.CharField(max_length=30, choices=FIXED_CHARGE_TYPES, default='flat_per_cycle')
    fixed_charge_rate = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('0.00'),
        help_text="Fixed charge in ₹ (or ₹ per kW if per_kw selected)"
    )

    electricity_duty_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('5.00'),
        help_text="Electricity tax / duty percentage (e.g., 5.0% on energy charges)"
    )

    free_units_per_cycle = models.PositiveIntegerField(
        default=100,
        help_text="Government free units per billing cycle (e.g. 100 free units in Tamil Nadu)"
    )
    subsidy_description = models.CharField(
        max_length=255, blank=True,
        default="TN Govt 100 Units Free Domestic Subsidy Scheme"
    )

    is_system_template = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-effective_from', 'name']

    def __str__(self):
        status = "Active" if self.is_active else "Archived"
        return f"{self.name} [{self.provider}] ({self.billing_frequency}) - {status}"

    def calculate_bill(self, units_consumed, sanctioned_load_kw=Decimal('3.0')):
        """
        Calculates a detailed, transparent electricity bill breakdown for given units and connected load.
        """
        units = Decimal(str(units_consumed)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        load = Decimal(str(sanctioned_load_kw)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        slabs = list(self.slabs.order_by('slab_order'))
        slab_breakdown = []
        gross_energy_charges = Decimal('0.00')

        remaining_units = units
        for slab in slabs:
            slab_capacity = None
            if slab.slab_max is not None:
                slab_capacity = slab.slab_max - slab.slab_min
            
            if slab_capacity is not None:
                units_in_slab = min(max(Decimal('0.00'), units - slab.slab_min), slab_capacity)
            else:
                # Open ended top slab
                units_in_slab = max(Decimal('0.00'), units - slab.slab_min)

            if units_in_slab > Decimal('0.00'):
                slab_amount = (units_in_slab * slab.rate_per_kwh).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                gross_energy_charges += slab_amount
                slab_breakdown.append({
                    'order': slab.slab_order,
                    'range': f"{slab.slab_min} - {slab.slab_max if slab.slab_max else 'above'} kWh",
                    'units': units_in_slab,
                    'rate': slab.rate_per_kwh,
                    'amount': slab_amount,
                })

        # Calculate government subsidy / free units
        subsidy_amount = Decimal('0.00')
        free_units = Decimal(str(self.free_units_per_cycle))
        if free_units > 0 and units > 0:
            # First free_units are subsidized at the first slab's rate
            first_slab = slabs[0] if slabs else None
            rate_for_subsidy = first_slab.rate_per_kwh if first_slab else Decimal('4.50')
            units_subsidized = min(units, free_units)
            subsidy_amount = (units_subsidized * rate_for_subsidy).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            # Cannot exceed gross energy charges
            subsidy_amount = min(subsidy_amount, gross_energy_charges)

        net_energy_charges = max(Decimal('0.00'), gross_energy_charges - subsidy_amount)

        # Fixed charges
        fixed_charges = Decimal('0.00')
        if self.fixed_charge_type == 'flat_per_cycle':
            fixed_charges = self.fixed_charge_rate
        elif self.fixed_charge_type == 'per_kw_sanctioned':
            fixed_charges = (self.fixed_charge_rate * load).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Additional charges (FPPCA, meter rent, etc.)
        additional_charges_list = []
        total_additional = Decimal('0.00')
        for charge in self.additional_charges.filter(is_active=True):
            if charge.charge_type == 'percentage':
                charge_amt = (net_energy_charges * (charge.charge_value / Decimal('100.0'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            elif charge.charge_type == 'per_kwh':
                charge_amt = (units * charge.charge_value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                charge_amt = charge.charge_value
            total_additional += charge_amt
            additional_charges_list.append({
                'name': charge.name,
                'type': charge.get_charge_type_display(),
                'value': charge.charge_value,
                'amount': charge_amt
            })

        # Electricity Duty / Tax
        duty_amount = Decimal('0.00')
        if self.electricity_duty_pct > 0:
            duty_amount = (net_energy_charges * (self.electricity_duty_pct / Decimal('100.0'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        total_bill_amount = (net_energy_charges + fixed_charges + total_additional + duty_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return {
            'units_consumed': units,
            'sanctioned_load_kw': load,
            'slab_breakdown': slab_breakdown,
            'gross_energy_charges': gross_energy_charges,
            'free_units': free_units,
            'subsidy_amount': subsidy_amount,
            'subsidy_description': self.subsidy_description,
            'net_energy_charges': net_energy_charges,
            'fixed_charges': fixed_charges,
            'additional_charges': additional_charges_list,
            'total_additional_charges': total_additional,
            'electricity_duty_pct': self.electricity_duty_pct,
            'electricity_duty_amount': duty_amount,
            'total_bill_amount': total_bill_amount,
            'tariff_name': self.name,
            'billing_frequency': self.billing_frequency,
        }


class TariffSlab(models.Model):
    tariff_plan = models.ForeignKey(TariffPlan, on_delete=models.CASCADE, related_name='slabs')
    slab_order = models.PositiveIntegerField(default=1)
    slab_min = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), help_text="Starting units (inclusive)")
    slab_max = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Ending units (inclusive), leave blank for above")
    rate_per_kwh = models.DecimalField(max_digits=6, decimal_places=2, help_text="Rate per unit in ₹")
    is_telescopic = models.BooleanField(default=True)

    class Meta:
        ordering = ['tariff_plan', 'slab_order']

    def __str__(self):
        max_str = f"{self.slab_max}" if self.slab_max is not None else "Above"
        return f"Slab {self.slab_order}: {self.slab_min} - {max_str} kWh @ ₹{self.rate_per_kwh}/kWh"


class TariffCharge(models.Model):
    CHARGE_TYPES = [
        ('percentage', 'Percentage on Energy Charges (%)'),
        ('per_kwh', 'Per Unit Consumption (₹/kWh)'),
        ('fixed_amount', 'Fixed Amount per Cycle (₹)'),
    ]

    tariff_plan = models.ForeignKey(TariffPlan, on_delete=models.CASCADE, related_name='additional_charges')
    name = models.CharField(max_length=120, help_text="e.g. Fuel Surcharge / FPPCA, Meter Rent")
    charge_type = models.CharField(max_length=20, choices=CHARGE_TYPES, default='fixed_amount')
    charge_value = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_charge_type_display()}: {self.charge_value})"


class TariffHistory(models.Model):
    tariff_plan = models.ForeignKey(TariffPlan, on_delete=models.CASCADE, related_name='change_history')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    change_summary = models.CharField(max_length=255)
    previous_snapshot = models.JSONField(default=dict, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']
