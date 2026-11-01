from django import forms
from .models import ElectricityBill
from tariffs.models import TariffPlan


class ElectricityBillForm(forms.ModelForm):
    class Meta:
        model = ElectricityBill
        fields = [
            'meter', 'tariff_plan', 'bill_number', 'billing_period_start', 'billing_period_end',
            'issue_date', 'due_date', 'payment_date', 'payment_status',
            'previous_reading', 'current_reading', 'total_units_kwh',
            'energy_charges', 'fixed_charges', 'duty_and_taxes', 'subsidies_and_adjustments',
            'total_bill_amount', 'actual_bill_amount', 'bill_document', 'notes'
        ]
        widgets = {
            'meter': forms.Select(attrs={'class': 'form-select'}),
            'tariff_plan': forms.Select(attrs={'class': 'form-select'}),
            'bill_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. TN-2026-OCT-1402'}),
            'billing_period_start': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'billing_period_end': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'previous_reading': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'current_reading': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'total_units_kwh': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'energy_charges': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'fixed_charges': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'duty_and_taxes': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'subsidies_and_adjustments': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'total_bill_amount': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'actual_bill_amount': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': 'Leave empty if unknown'}),
            'bill_document': forms.FileInput(attrs={'class': 'form-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        household = kwargs.pop('household', None)
        super().__init__(*args, **kwargs)
        if household:
            self.fields['meter'].queryset = household.meters.filter(meter_status='Active')
        self.fields['tariff_plan'].queryset = TariffPlan.objects.filter(is_active=True)


class BillCalculatorForm(forms.Form):
    meter = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="-- Select Meter (Optional) --",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tariff_plan = forms.ModelChoiceField(
        queryset=TariffPlan.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    units_consumed = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '1', 'placeholder': 'e.g. 350'})
    )
    sanctioned_load_kw = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        initial=3.0,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'})
    )

    def __init__(self, *args, **kwargs):
        household = kwargs.pop('household', None)
        super().__init__(*args, **kwargs)
        if household:
            self.fields['meter'].queryset = household.meters.filter(meter_status='Active')
            self.fields['sanctioned_load_kw'].initial = household.sanctioned_load_kw
            default_tariff = household.meters.first().tariff_plan if household.meters.exists() else None
            if default_tariff:
                self.fields['tariff_plan'].initial = default_tariff
