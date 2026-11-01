from django import forms
from .models import Household, HouseholdMember
from django.contrib.auth.models import User


class HouseholdForm(forms.ModelForm):
    class Meta:
        model = Household
        fields = [
            'name', 'property_type', 'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country',
            'occupants', 'sanctioned_load_kw', 'monthly_budget_amount', 'billing_cycle_day'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Primary Residence'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Street address'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Locality / Area'}),
            'city': forms.TextInput(attrs={'class': 'form-input'}),
            'state': forms.TextInput(attrs={'class': 'form-input'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-input'}),
            'country': forms.TextInput(attrs={'class': 'form-input'}),
            'occupants': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'sanctioned_load_kw': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'monthly_budget_amount': forms.NumberInput(attrs={'class': 'form-input', 'step': '50'}),
            'billing_cycle_day': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 31}),
        }


class HouseholdMemberForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter existing username'}))

    class Meta:
        model = HouseholdMember
        fields = ['role', 'can_edit_readings', 'can_manage_tariffs', 'can_manage_budget']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError(f"User '{username}' was not found.")
