from django.db import models
from decimal import Decimal


class ForecastRecord(models.Model):
    household = models.ForeignKey('households.Household', on_delete=models.CASCADE, related_name='forecasts')
    meter = models.ForeignKey('meters.ElectricityMeter', on_delete=models.SET_NULL, null=True, blank=True, related_name='forecasts')
    forecast_date = models.DateField(auto_now_add=True)
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    days_elapsed = models.PositiveIntegerField()
    days_remaining = models.PositiveIntegerField()
    current_consumed_kwh = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    projected_total_kwh = models.DecimalField(max_digits=10, decimal_places=2)
    projected_cost_amount = models.DecimalField(max_digits=10, decimal_places=2)
    daily_average_kwh = models.DecimalField(max_digits=8, decimal_places=2)
    confidence_score_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('80.00'))
    method_used = models.CharField(max_length=100, default='Statistical Moving Average')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Forecast for {self.household.name}: {self.projected_total_kwh} kWh (~₹{self.projected_cost_amount})"


class SavingsScenario(models.Model):
    household = models.ForeignKey('households.Household', on_delete=models.CASCADE, related_name='savings_scenarios')
    appliance = models.ForeignKey('appliances.Appliance', on_delete=models.CASCADE, null=True, blank=True, related_name='scenarios')
    name = models.CharField(max_length=150)
    proposed_daily_hours = models.DecimalField(max_digits=4, decimal_places=2)
    proposed_power_watts = models.PositiveIntegerField(null=True, blank=True)
    monthly_kwh_saved = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_cost_saved = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - Saves {self.monthly_kwh_saved} kWh (₹{self.monthly_cost_saved}/mo)"
