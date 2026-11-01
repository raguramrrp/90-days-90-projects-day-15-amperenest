from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    THEME_CHOICES = [
        ('light', 'Professional Light'),
        ('dark', 'Technical Charcoal Dark'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True)
    theme_preference = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    notification_email = models.BooleanField(default=True, help_text="Receive email alerts for bill due dates and budget warnings")
    notification_app = models.BooleanField(default=True, help_text="Show in-app notification alerts")
    default_household = models.ForeignKey(
        'households.Household',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_users'
    )
    currency_symbol = models.CharField(max_length=5, default='₹')
    currency_code = models.CharField(max_length=5, default='INR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
