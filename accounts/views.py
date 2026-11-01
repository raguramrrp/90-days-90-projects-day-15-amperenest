from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm, PreferencesForm
from households.models import Household
from tariffs.services import create_default_tamilnadu_tariff


def login_view(request):
    if settings.DEBUG and request.GET.get('demo_auth') == '1':
        from django.contrib.auth.models import User
        demo = User.objects.filter(username='demouser').first()
        if demo:
            login(request, demo)
            return redirect(request.GET.get('next') or 'core:dashboard')

    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            return redirect(next_url or 'core:dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Ensure default tariff exists
            tariff = create_default_tamilnadu_tariff(user=user)

            # Create default household for new user
            household = Household.objects.create(
                created_by=user,
                name=f"{user.username.capitalize()}'s Residence",
                property_type='independent_house',
                city='Chennai',
                state='Tamil Nadu',
                sanctioned_load_kw=3.00,
                monthly_budget_amount=2000.00
            )

            # Auto create primary meter
            from meters.models import ElectricityMeter
            ElectricityMeter.objects.create(
                household=household,
                meter_name="Main Digital Meter",
                meter_number=f"MTR-{user.id:04d}-01",
                service_number=f"042010{user.id:04d}",
                electricity_provider="TANGEDCO / TNPDCL",
                consumer_category="residential_domestic",
                sanctioned_load_kw=3.00,
                tariff_plan=tariff,
                meter_status="Active"
            )

            user.profile.default_household = household
            user.profile.save()

            login(request, user)
            request.session['active_household_id'] = household.id
            messages.success(request, "Registration successful! Your primary household has been created.")
            return redirect('core:dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile, user=request.user)

    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})


@login_required
def preferences_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = PreferencesForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "System preferences updated.")
            return redirect('accounts:preferences')
    else:
        form = PreferencesForm(instance=profile, user=request.user)

    return render(request, 'accounts/preferences.html', {'form': form})
