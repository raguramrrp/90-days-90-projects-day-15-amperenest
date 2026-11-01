from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal

from consumption.services import get_billing_cycle_boundaries, get_household_consumption_stats
from consumption.models import MeterReading
from tariffs.services import get_tariff_for_date
from billing.models import ElectricityBill
from appliances.models import Appliance
from budgets.models import EnergyBudget
from alerts.services import evaluate_household_alerts
from analytics.services import get_dashboard_chart_data, generate_energy_insights, generate_billing_cycle_forecast


from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User

@login_required
def dashboard(request):
    if settings.DEBUG and request.GET.get('demo_auth') == '1':
        demo = User.objects.filter(username='demouser').first()
        if demo and request.user != demo:
            login(request, demo)
    household = request.active_household
    if not household:
        # If user has no households, redirect to creation
        if not request.accessible_households.exists():
            return redirect('households:create')
        # Otherwise pick the first accessible one
        first_h = request.accessible_households.first()
        request.session['active_household_id'] = first_h.id
        household = first_h

    today = timezone.localdate()

    # 1. Evaluate alert engine for real notifications
    evaluate_household_alerts(household)

    # 2. Cycle boundaries & consumption
    cycle_info = get_billing_cycle_boundaries(household, today)
    meters = household.meters.filter(meter_status='Active')

    cycle_readings = MeterReading.objects.filter(
        meter__in=meters,
        reading_date__gte=cycle_info['cycle_start'],
        reading_date__lte=today,
        is_flagged_inversion=False
    )
    cycle_kwh = sum(r.consumption_kwh for r in cycle_readings)

    # Daily average
    days_elapsed = cycle_info['days_elapsed']
    daily_avg_kwh = (Decimal(str(cycle_kwh)) / Decimal(str(days_elapsed))).quantize(Decimal('0.01')) if days_elapsed > 0 else Decimal('0.00')

    # 3. Bill estimation
    primary_meter = meters.first()
    tariff = get_tariff_for_date(primary_meter, today)
    estimated_bill_amt = Decimal('0.00')
    bill_calc = None
    if tariff and cycle_kwh > 0:
        bill_calc = tariff.calculate_bill(cycle_kwh, household.sanctioned_load_kw)
        estimated_bill_amt = bill_calc['total_bill_amount']

    # 4. Budget
    budget_amt = household.monthly_budget_amount
    remaining_budget = max(Decimal('0.00'), budget_amt - estimated_bill_amt)
    budget_utilization_pct = ((estimated_bill_amt / budget_amt) * Decimal('100.0')) if budget_amt > 0 else Decimal('0.0')

    # 5. Previous bill
    previous_bill = ElectricityBill.objects.filter(meter__in=meters).exclude(is_estimated_bill=True).order_by('-billing_period_end').first()

    # 6. Upcoming due bill
    upcoming_bill = ElectricityBill.objects.filter(
        meter__in=meters,
        payment_status__in=['Pending', 'Overdue']
    ).order_by('due_date').first()

    # 7. Top 3 power drainers
    top_appliances = household.appliances.filter(is_active=True).order_by('-rated_power_watts')[:4]

    # 8. Chart data & actionable insights
    chart_data = get_dashboard_chart_data(household)
    insights = generate_energy_insights(household)[:3]
    forecast = generate_billing_cycle_forecast(household)

    # 9. Latest meter reading
    latest_reading = MeterReading.objects.filter(meter__in=meters).order_by('-reading_date').first()

    return render(request, 'core/dashboard.html', {
        'household': household,
        'meters': meters,
        'cycle_info': cycle_info,
        'cycle_kwh': cycle_kwh,
        'daily_avg_kwh': daily_avg_kwh,
        'estimated_bill_amt': estimated_bill_amt,
        'bill_calc': bill_calc,
        'budget_amt': budget_amt,
        'remaining_budget': remaining_budget,
        'budget_utilization_pct': min(Decimal('100.0'), budget_utilization_pct).quantize(Decimal('0.1')),
        'previous_bill': previous_bill,
        'upcoming_bill': upcoming_bill,
        'top_appliances': top_appliances,
        'chart_data': chart_data,
        'insights': insights,
        'forecast': forecast,
        'latest_reading': latest_reading,
        'tariff': tariff,
    })
