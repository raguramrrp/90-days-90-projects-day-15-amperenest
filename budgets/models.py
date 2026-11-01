from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class EnergyBudget(models.Model):
    household = models.ForeignKey('households.Household', on_delete=models.CASCADE, related_name='budgets')
    month = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.PositiveIntegerField()
    monthly_budget_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('2000.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Target electricity expense for this month in ₹"
    )
    target_consumption_kwh = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('250.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Target consumption cap in kWh"
    )
    daily_target_kwh = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('8.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Target average daily consumption in kWh"
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', '-month']
        unique_together = ('household', 'month', 'year')

    def __str__(self):
        return f"{self.household.name} - {self.month:02d}/{self.year}: ₹{self.monthly_budget_amount} ({self.target_consumption_kwh} kWh)"


class EnergyGoal(models.Model):
    STATUS_CHOICES = [
        ('In Progress', 'In Progress'),
        ('Achieved', 'Achieved'),
        ('Missed', 'Missed Target'),
        ('Paused', 'Paused'),
    ]

    GOAL_TYPES = [
        ('consumption_target', 'Total Consumption Cap (kWh)'),
        ('budget_limit', 'Expense Limit (₹)'),
        ('appliance_reduction', 'Appliance Usage Reduction (Hours)'),
        ('general', 'General Efficiency Target'),
    ]

    household = models.ForeignKey('households.Household', on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=150, help_text="e.g. Keep summer AC electricity cost under ₹1,500")
    goal_type = models.CharField(max_length=30, choices=GOAL_TYPES, default='budget_limit')
    target_value = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    unit = models.CharField(max_length=20, default='₹')
    start_date = models.DateField()
    target_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='In Progress')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-target_date', '-id']

    def __str__(self):
        return f"{self.title} - Target: {self.target_value} {self.unit} ({self.status})"

    @property
    def progress_percentage(self):
        if self.target_value > 0:
            pct = (self.current_value / self.target_value) * Decimal('100.0')
            return min(Decimal('100.0'), pct).quantize(Decimal('0.1'))
        return Decimal('0.0')
