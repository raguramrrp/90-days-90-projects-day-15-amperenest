from django import forms
from .models import EnergyAlertRule


class EnergyAlertRuleForm(forms.ModelForm):
    class Meta:
        model = EnergyAlertRule
        fields = ['rule_type', 'threshold_value', 'is_enabled']
        widgets = {
            'rule_type': forms.Select(attrs={'class': 'form-select'}),
            'threshold_value': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
