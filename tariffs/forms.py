from django import forms
from .models import TariffPlan, TariffSlab, TariffCharge


class TariffPlanForm(forms.ModelForm):
    class Meta:
        model = TariffPlan
        fields = [
            'name', 'provider', 'state', 'consumer_category', 'billing_frequency',
            'effective_from', 'effective_to', 'is_active', 'fixed_charge_type',
            'fixed_charge_rate', 'electricity_duty_pct', 'free_units_per_cycle',
            'subsidy_description', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. TANGEDCO Domestic LT-1A'}),
            'provider': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. TANGEDCO / TNPDCL'}),
            'state': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Tamil Nadu'}),
            'consumer_category': forms.TextInput(attrs={'class': 'form-input'}),
            'billing_frequency': forms.Select(attrs={'class': 'form-select'}),
            'effective_from': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'effective_to': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'fixed_charge_type': forms.Select(attrs={'class': 'form-select'}),
            'fixed_charge_rate': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'electricity_duty_pct': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'free_units_per_cycle': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'subsidy_description': forms.TextInput(attrs={'class': 'form-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }


class TariffSlabForm(forms.ModelForm):
    class Meta:
        model = TariffSlab
        fields = ['slab_order', 'slab_min', 'slab_max', 'rate_per_kwh', 'is_telescopic']
        widgets = {
            'slab_order': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'slab_min': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'slab_max': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': 'Leave empty for above'}),
            'rate_per_kwh': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
        }


class TariffChargeForm(forms.ModelForm):
    class Meta:
        model = TariffCharge
        fields = ['name', 'charge_type', 'charge_value', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Fuel Surcharge / FPPCA'}),
            'charge_type': forms.Select(attrs={'class': 'form-select'}),
            'charge_value': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
        }
