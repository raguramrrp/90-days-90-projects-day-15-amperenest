from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal

from households.models import Household
from meters.models import ElectricityMeter


class SecurityAndIsolationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(username="usera", password="password_a")
        self.user_b = User.objects.create_user(username="userb", password="password_b")

        self.household_a = Household.objects.create(
            created_by=self.user_a,
            name="User A Private Residence",
            sanctioned_load_kw=Decimal('3.00')
        )
        self.meter_a = ElectricityMeter.objects.create(
            household=self.household_a,
            meter_name="User A Meter",
            meter_number="MTR-A",
            sanctioned_load_kw=Decimal('3.00')
        )

        self.household_b = Household.objects.create(
            created_by=self.user_b,
            name="User B Private Residence",
            sanctioned_load_kw=Decimal('5.00')
        )

    def test_unauthenticated_redirect(self):
        """Unauthenticated requests must redirect to login."""
        res = self.client.get(reverse('core:dashboard'))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('accounts:login'), res.url)

    def test_user_cannot_access_other_household(self):
        """User B must be forbidden from accessing User A's private household."""
        self.client.login(username="userb", password="password_b")
        res = self.client.get(reverse('households:detail', kwargs={'pk': self.household_a.id}))
        self.assertEqual(res.status_code, 403)

    def test_user_cannot_edit_other_household(self):
        """User B cannot edit User A's household settings."""
        self.client.login(username="userb", password="password_b")
        res = self.client.get(reverse('households:edit', kwargs={'pk': self.household_a.id}))
        self.assertEqual(res.status_code, 403)

    def test_user_cannot_view_other_meter(self):
        """User B cannot view User A's meter details."""
        self.client.login(username="userb", password="password_b")
        res = self.client.get(reverse('meters:detail', kwargs={'pk': self.meter_a.id}))
        self.assertEqual(res.status_code, 403)
