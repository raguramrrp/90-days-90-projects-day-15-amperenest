from django import forms
from .models import Appliance


class ApplianceForm(forms.ModelForm):
    class Meta:
        model = Appliance
        fields = [
            'name', 'category', 'brand', 'model_name', 'rated_power_watts',
            'quantity', 'daily_operating_hours', 'days_used_per_month',
            'standby_power_watts', 'energy_star_rating', 'is_active', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Master Bedroom Inverter AC 1.5T'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Daikin, LG, Samsung'}),
            'model_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional model number'}),
            'rated_power_watts': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'placeholder': 'Watts'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'daily_operating_hours': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.25', 'min': 0, 'max': 24}),
            'days_used_per_month': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 31}),
            'standby_power_watts': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'min': 0}),
            'energy_star_rating': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 5, 'placeholder': '1-5 Stars'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }
