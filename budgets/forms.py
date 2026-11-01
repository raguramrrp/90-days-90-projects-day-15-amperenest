from django import forms
from .models import EnergyBudget, EnergyGoal


class EnergyBudgetForm(forms.ModelForm):
    class Meta:
        model = EnergyBudget
        fields = ['month', 'year', 'monthly_budget_amount', 'target_consumption_kwh', 'daily_target_kwh', 'notes']
        widgets = {
            'month': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 12}),
            'year': forms.NumberInput(attrs={'class': 'form-input', 'min': 2020, 'max': 2035}),
            'monthly_budget_amount': forms.NumberInput(attrs={'class': 'form-input', 'step': '50', 'placeholder': '₹'}),
            'target_consumption_kwh': forms.NumberInput(attrs={'class': 'form-input', 'step': '5', 'placeholder': 'kWh'}),
            'daily_target_kwh': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'}),
            'notes': forms.TextInput(attrs={'class': 'form-input'}),
        }


class EnergyGoalForm(forms.ModelForm):
    class Meta:
        model = EnergyGoal
        fields = ['title', 'goal_type', 'target_value', 'unit', 'start_date', 'target_date', 'status', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Keep summer AC bill under ₹1,500'}),
            'goal_type': forms.Select(attrs={'class': 'form-select'}),
            'target_value': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'unit': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '₹, kWh, Hours'}),
            'start_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'target_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }
