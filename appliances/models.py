from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal, ROUND_HALF_UP


class Appliance(models.Model):
    CATEGORIES = [
        ('air_conditioner', 'Air Conditioner (Split / Window)'),
        ('refrigerator', 'Refrigerator (Single / Double Door)'),
        ('washing_machine', 'Washing Machine'),
        ('ceiling_fan', 'Ceiling Fan (Standard / BLDC)'),
        ('water_heater', 'Water Heater / Geyser'),
        ('water_pump', 'Water Pump / Submersible Motor'),
        ('television', 'Television / Home Entertainment'),
        ('microwave', 'Microwave Oven / OTG'),
        ('computer_laptop', 'Computer / Laptop / Workstation'),
        ('lighting', 'Lighting / Bulbs / Tube Lights'),
        ('ev_charger', 'Electric Vehicle (EV) Charger'),
        ('induction_cooktop', 'Induction Cooktop / Electric Stove'),
        ('other', 'Other Household Appliance'),
    ]

    household = models.ForeignKey('households.Household', on_delete=models.CASCADE, related_name='appliances')
    name = models.CharField(max_length=150, help_text="e.g. Master Bedroom Inverter AC 1.5T")
    category = models.CharField(max_length=40, choices=CATEGORIES, default='air_conditioner')
    brand = models.CharField(max_length=80, blank=True)
    model_name = models.CharField(max_length=100, blank=True)

    rated_power_watts = models.PositiveIntegerField(
        default=1000,
        validators=[MinValueValidator(1)],
        help_text="Rated nameplate power in Watts (e.g. 1500 for AC, 75 for standard fan, 28 for BLDC)"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of identical appliances in use"
    )
    daily_operating_hours = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal('4.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('24.00'))],
        help_text="Average operating hours per day (0.0 to 24.0)"
    )
    days_used_per_month = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Operating days in a typical month (1-31)"
    )
    standby_power_watts = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Standby idle power drawn when plugged in but turned off (Watts)"
    )
    energy_star_rating = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="BEE Star Rating (1 to 5 Stars)"
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', 'category', 'name']

    def __str__(self):
        return f"{self.name} ({self.quantity}x {self.rated_power_watts}W) - {self.household.name}"

    @property
    def daily_consumption_kwh(self):
        """
        Estimated daily consumption in kWh = (Watts * hours * quantity) / 1000 + standby
        """
        active_hours = self.daily_operating_hours
        idle_hours = max(Decimal('0.00'), Decimal('24.00') - active_hours)

        watts = Decimal(self.rated_power_watts) * Decimal(self.quantity)
        standby = Decimal(str(self.standby_power_watts)) * Decimal(self.quantity)

        active_kwh = (watts * active_hours) / Decimal('1000.0')
        idle_kwh = (standby * idle_hours) / Decimal('1000.0')

        return (active_kwh + idle_kwh).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def monthly_consumption_kwh(self):
        """
        Estimated monthly consumption in kWh = daily kWh * days used per month
        """
        return (self.daily_consumption_kwh * Decimal(self.days_used_per_month)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def estimate_monthly_cost(self, rate_per_kwh=Decimal('5.50')):
        """
        Estimated monthly cost in ₹ at given average per-unit rate
        """
        rate = Decimal(str(rate_per_kwh))
        return (self.monthly_consumption_kwh * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def simulate_savings(self, proposed_hours, proposed_watts=None, rate_per_kwh=Decimal('5.50')):
        """
        Calculates hypothetical savings from reducing hours or switching to more efficient unit.
        """
        orig_monthly_kwh = self.monthly_consumption_kwh
        new_watts = Decimal(proposed_watts) if proposed_watts else Decimal(self.rated_power_watts)
        new_hours = Decimal(str(proposed_hours))

        new_daily_kwh = (new_watts * Decimal(self.quantity) * new_hours) / Decimal('1000.0')
        new_monthly_kwh = (new_daily_kwh * Decimal(self.days_used_per_month)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        kwh_saved = max(Decimal('0.00'), orig_monthly_kwh - new_monthly_kwh)
        cost_saved = (kwh_saved * Decimal(str(rate_per_kwh))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return {
            'original_monthly_kwh': orig_monthly_kwh,
            'proposed_monthly_kwh': new_monthly_kwh,
            'kwh_saved': kwh_saved,
            'cost_saved': cost_saved,
            'rate_used': rate_per_kwh
        }
