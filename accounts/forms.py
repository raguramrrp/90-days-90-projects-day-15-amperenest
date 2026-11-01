from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
from households.models import Household


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Create secure password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm password'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Choose username'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'name@example.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last name'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-input'}))

    class Meta:
        model = UserProfile
        fields = ['phone_number', 'theme_preference', 'currency_symbol', 'notification_email', 'notification_app', 'default_household']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+91 98765 43210'}),
            'theme_preference': forms.Select(attrs={'class': 'form-select'}),
            'currency_symbol': forms.TextInput(attrs={'class': 'form-input', 'style': 'max-width: 100px;'}),
            'default_household': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            from households.middleware import models_q_user_households
            self.fields['default_household'].queryset = Household.objects.filter(
                models_q_user_households(user), is_archived=False
            )


class PreferencesForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['theme_preference', 'currency_symbol', 'notification_email', 'notification_app', 'default_household']
        widgets = {
            'theme_preference': forms.Select(attrs={'class': 'form-select'}),
            'currency_symbol': forms.TextInput(attrs={'class': 'form-input', 'style': 'max-width: 100px;'}),
            'default_household': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            from households.middleware import models_q_user_households
            self.fields['default_household'].queryset = Household.objects.filter(
                models_q_user_households(user), is_archived=False
            )
