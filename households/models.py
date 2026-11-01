from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Household(models.Model):
    PROPERTY_TYPES = [
        ('apartment', 'Apartment / Flat'),
        ('independent_house', 'Independent House'),
        ('villa', 'Residential Villa'),
        ('farmhouse', 'Farmhouse / Rural Property'),
        ('commercial_home', 'Home Office / Clinic / Shop'),
        ('other', 'Other Residential Property'),
    ]

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_households')
    name = models.CharField(max_length=120, help_text="e.g. Primary Residence, Chennai Flat, Beach Villa")
    property_type = models.CharField(max_length=30, choices=PROPERTY_TYPES, default='independent_house')
    address_line1 = models.CharField(max_length=200, blank=True)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, default='Chennai')
    state = models.CharField(max_length=100, default='Tamil Nadu')
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=60, default='India')

    occupants = models.PositiveIntegerField(default=3, validators=[MinValueValidator(1)])
    sanctioned_load_kw = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=3.00,
        validators=[MinValueValidator(0.1)],
        help_text="Sanctioned connected load in kW (e.g., 3.0, 5.0, 7.5 kW)"
    )
    monthly_budget_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=2000.00,
        validators=[MinValueValidator(0.0)],
        help_text="Monthly electricity expenditure target in ₹"
    )
    billing_cycle_day = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Day of the month the billing cycle begins (1-31)"
    )
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.city}, {self.state})"

    def user_has_permission(self, user, permission='view'):
        if self.created_by == user:
            return True
        membership = self.memberships.filter(user=user).first()
        if not membership:
            return False
        if membership.role in ['Owner', 'Admin']:
            return True
        if permission == 'edit_reading' and membership.can_edit_readings:
            return True
        if permission == 'manage_tariff' and membership.can_manage_tariffs:
            return True
        if permission == 'manage_budget' and membership.can_manage_budget:
            return True
        if permission == 'view':
            return True
        return False


class HouseholdMember(models.Model):
    ROLE_CHOICES = [
        ('Owner', 'Owner (Full Access)'),
        ('Admin', 'Administrator (Manage all data)'),
        ('Member', 'Member (Can record & edit readings)'),
        ('Viewer', 'Viewer (Read-only access)'),
    ]

    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='household_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Member')
    can_edit_readings = models.BooleanField(default=True)
    can_manage_tariffs = models.BooleanField(default=False)
    can_manage_budget = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('household', 'user')
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} - {self.household.name} ({self.role})"
