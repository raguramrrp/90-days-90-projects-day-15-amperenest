from django import forms
from django.utils import timezone
from .models import MeterReading


class MeterReadingForm(forms.ModelForm):
    class Meta:
        model = MeterReading
        fields = [
            'meter', 'reading_date', 'reading_time', 'reading_value',
            'reading_type', 'is_meter_reset_or_replacement', 'supporting_image', 'notes'
        ]
        widgets = {
            'meter': forms.Select(attrs={'class': 'form-select'}),
            'reading_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'reading_time': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'reading_value': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': 'Dial reading in kWh'}),
            'reading_type': forms.Select(attrs={'class': 'form-select'}),
            'supporting_image': forms.FileInput(attrs={'class': 'form-input'}),
            'notes': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional notes or observations'}),
        }

    def __init__(self, *args, **kwargs):
        household = kwargs.pop('household', None)
        super().__init__(*args, **kwargs)
        if household:
            self.fields['meter'].queryset = household.meters.filter(meter_status='Active')
        if not self.initial.get('reading_date'):
            self.initial['reading_date'] = timezone.localdate()


class DirectConsumptionForm(forms.ModelForm):
    """Direct period consumption entry mode (Method 2)"""
    class Meta:
        model = MeterReading
        fields = ['meter', 'reading_date', 'consumption_kwh', 'notes']
        widgets = {
            'meter': forms.Select(attrs={'class': 'form-select'}),
            'reading_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'consumption_kwh': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': 'Direct consumption in kWh'}),
            'notes': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Measured via smart plug'}),
        }

    def __init__(self, *args, **kwargs):
        household = kwargs.pop('household', None)
        super().__init__(*args, **kwargs)
        if household:
            self.fields['meter'].queryset = household.meters.filter(meter_status='Active')
        if not self.initial.get('reading_date'):
            self.initial['reading_date'] = timezone.localdate()


class ReadingImportForm(forms.Form):
    meter = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="-- Auto-match from file or select meter --",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    import_file = forms.FileField(
        label="CSV or Excel File (.csv, .xlsx)",
        widget=forms.FileInput(attrs={'class': 'form-input', 'accept': '.csv, .xlsx, .xls'})
    )

    def __init__(self, *args, **kwargs):
        household = kwargs.pop('household', None)
        super().__init__(*args, **kwargs)
        if household:
            self.fields['meter'].queryset = household.meters.all()
