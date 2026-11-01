from django.db import models
from decimal import Decimal


class EnergyAlertRule(models.Model):
    RULE_TYPES = [
        ('high_daily_kwh', 'High Daily Consumption (exceeds threshold kWh)'),
        ('unusual_spike_pct', 'Unusual Consumption Surge (> threshold % above 7-day avg)'),
        ('budget_threshold_pct', 'Monthly Budget Threshold Reached (> threshold % of budget)'),
        ('projected_overrun', 'Projected Budget Overrun (> monthly budget amount)'),
        ('bill_due_soon', 'Upcoming Bill Due Date (due within threshold days)'),
        ('bill_overdue', 'Overdue Bill Unpaid'),
        ('missing_reading_days', 'Missing Meter Reading (> threshold days since last reading)'),
        ('inconsistent_reading', 'Inconsistent / Decreasing Meter Reading Detected'),
    ]

    household = models.ForeignKey('households.Household', on_delete=models.CASCADE, related_name='alert_rules')
    rule_type = models.CharField(max_length=30, choices=RULE_TYPES)
    threshold_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text="Numeric threshold trigger (e.g. 15.0 for 15 kWh, 80.0 for 80% budget, 3 for 3 days)"
    )
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['household', 'rule_type']
        unique_together = ('household', 'rule_type')

    def __str__(self):
        return f"{self.household.name}: {self.get_rule_type_display()} (Threshold: {self.threshold_value})"


class EnergyAlert(models.Model):
    SEVERITY_CHOICES = [
        ('info', 'Informational Notice'),
        ('warning', 'Consumption / Budget Warning'),
        ('danger', 'Critical Overrun / Overdue Alert'),
    ]

    household = models.ForeignKey('households.Household', on_delete=models.CASCADE, related_name='alerts')
    alert_rule = models.ForeignKey(EnergyAlertRule, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_alerts')
    alert_type = models.CharField(max_length=40)
    title = models.CharField(max_length=150)
    message = models.TextField()
    severity = models.CharField(max_length=15, choices=SEVERITY_CHOICES, default='warning')
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.severity.upper()}] {self.household.name}: {self.title} ({self.created_at.strftime('%Y-%m-%d')})"
