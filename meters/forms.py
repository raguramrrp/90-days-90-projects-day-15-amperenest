from django import forms
from .models import ElectricityMeter
from tariffs.models import TariffPlan


class ElectricityMeterForm(forms.ModelForm):
    class Meta:
        model = ElectricityMeter
        fields = [
            'meter_name', 'meter_number', 'service_number', 'electricity_provider',
            'consumer_category', 'connection_type', 'sanctioned_load_kw',
            'installation_date', 'reading_unit', 'billing_cycle', 'tariff_plan',
            'meter_status', 'dial_digits', 'notes'
        ]
        widgets = {
            'meter_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Main Digital Meter'}),
            'meter_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 04-201-008-1422'}),
            'service_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Consumer / Account Number'}),
            'electricity_provider': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'TANGEDCO / TNPDCL'}),
            'consumer_category': forms.Select(attrs={'class': 'form-select'}),
            'connection_type': forms.Select(attrs={'class': 'form-select'}),
            'sanctioned_load_kw': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'installation_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'reading_unit': forms.TextInput(attrs={'class': 'form-input', 'readonly': 'readonly'}),
            'billing_cycle': forms.Select(attrs={'class': 'form-select'}),
            'tariff_plan': forms.Select(attrs={'class': 'form-select'}),
            'meter_status': forms.Select(attrs={'class': 'form-select'}),
            'dial_digits': forms.NumberInput(attrs={'class': 'form-input', 'min': 4, 'max': 8}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tariff_plan'].queryset = TariffPlan.objects.filter(is_active=True)
