from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from decimal import Decimal
from .models import ForecastRecord, SavingsScenario
from .services import generate_billing_cycle_forecast, generate_energy_insights, get_dashboard_chart_data
from appliances.models import Appliance
from consumption.models import MeterReading
from billing.models import ElectricityBill
from core.reports import export_readings_csv, export_readings_excel, export_bills_excel, export_appliances_excel


@login_required
def consumption_trends(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    chart_data = get_dashboard_chart_data(household)
    insights = generate_energy_insights(household)

    return render(request, 'analytics/trends.html', {
        'household': household,
        'chart_data': chart_data,
        'insights': insights,
    })


@login_required
def cost_analysis(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    meters = household.meters.all()
    bills = ElectricityBill.objects.filter(meter__in=meters).order_by('-billing_period_end')

    total_spent = sum(b.total_bill_amount for b in bills if b.payment_status == 'Paid')
    avg_bill = (total_spent / Decimal(bills.count())) if bills.count() > 0 else Decimal('0.00')

    chart_data = get_dashboard_chart_data(household)

    return render(request, 'analytics/costs.html', {
        'household': household,
        'bills': bills,
        'total_spent': total_spent,
        'avg_bill': avg_bill,
        'chart_data': chart_data,
    })


@login_required
def forecasting_view(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    forecast = generate_billing_cycle_forecast(household)

    # Save to history if sufficient data
    if forecast.get('has_sufficient_data') and request.method == 'POST':
        c_info = forecast['cycle_info']
        ForecastRecord.objects.create(
            household=household,
            billing_period_start=c_info['cycle_start'],
            billing_period_end=c_info['cycle_end'],
            days_elapsed=c_info['days_elapsed'],
            days_remaining=c_info['days_remaining'],
            current_consumed_kwh=forecast['current_consumed_kwh'],
            projected_total_kwh=forecast['projected_total_kwh'],
            projected_cost_amount=forecast['projected_bill_amount'],
            daily_average_kwh=forecast['daily_average_kwh'],
            confidence_score_pct=forecast['confidence_score_pct'],
            method_used='Statistical Moving Average with Cycle Boundaries'
        )
        messages.success(request, "Forecast projection snapshot archived.")

    history = ForecastRecord.objects.filter(household=household).order_by('-created_at')[:5]

    return render(request, 'analytics/forecasting.html', {
        'household': household,
        'forecast': forecast,
        'history': history,
    })


@login_required
def savings_planner(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    appliances = household.appliances.filter(is_active=True).order_by('-rated_power_watts')
    sim_result = None

    selected_appliance_id = request.GET.get('appliance')
    proposed_hours_raw = request.GET.get('proposed_hours')

    if selected_appliance_id and proposed_hours_raw:
        appliance = get_object_or_404(Appliance, pk=selected_appliance_id, household=household)
        try:
            proposed_hours = Decimal(proposed_hours_raw)
            sim_result = appliance.simulate_savings(proposed_hours)
            sim_result['appliance'] = appliance
            sim_result['proposed_hours'] = proposed_hours
        except Exception:
            pass

    scenarios = household.savings_scenarios.all().order_by('-created_at')

    return render(request, 'analytics/savings_planner.html', {
        'household': household,
        'appliances': appliances,
        'selected_appliance_id': int(selected_appliance_id) if selected_appliance_id else None,
        'proposed_hours_raw': proposed_hours_raw,
        'sim_result': sim_result,
        'scenarios': scenarios,
    })


@login_required
def savings_scenario_save(request):
    household = request.active_household
    if not household or request.method != 'POST':
        return redirect('analytics:savings_planner')

    appliance_id = request.POST.get('appliance_id')
    name = request.POST.get('name')
    proposed_hours = Decimal(request.POST.get('proposed_hours', '0'))
    kwh_saved = Decimal(request.POST.get('kwh_saved', '0'))
    cost_saved = Decimal(request.POST.get('cost_saved', '0'))

    appliance = get_object_or_404(Appliance, pk=appliance_id, household=household)
    SavingsScenario.objects.create(
        household=household,
        appliance=appliance,
        name=name or f"Reduce {appliance.name} to {proposed_hours}h/day",
        proposed_daily_hours=proposed_hours,
        proposed_power_watts=appliance.rated_power_watts,
        monthly_kwh_saved=kwh_saved,
        monthly_cost_saved=cost_saved
    )
    messages.success(request, f"Scenario '{name}' saved.")
    return redirect('analytics:savings_planner')


@login_required
def reports_hub(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    readings_count = MeterReading.objects.filter(meter__household=household).count()
    bills_count = ElectricityBill.objects.filter(meter__household=household).count()
    appliances_count = household.appliances.count()

    return render(request, 'analytics/reports.html', {
        'household': household,
        'readings_count': readings_count,
        'bills_count': bills_count,
        'appliances_count': appliances_count,
    })


@login_required
def export_readings_csv_action(request):
    household = request.active_household
    readings = MeterReading.objects.filter(meter__household=household).order_by('-reading_date')
    return export_readings_csv(readings, filename=f"readings_{household.name.replace(' ', '_')}.csv")


@login_required
def export_readings_excel_action(request):
    household = request.active_household
    readings = MeterReading.objects.filter(meter__household=household).order_by('-reading_date')
    return export_readings_excel(readings, filename=f"readings_{household.name.replace(' ', '_')}.xlsx")


@login_required
def export_bills_excel_action(request):
    household = request.active_household
    bills = ElectricityBill.objects.filter(meter__household=household).order_by('-billing_period_end')
    return export_bills_excel(bills, filename=f"bills_{household.name.replace(' ', '_')}.xlsx")


@login_required
def export_appliances_excel_action(request):
    household = request.active_household
    appliances = household.appliances.all().order_by('-rated_power_watts')
    return export_appliances_excel(appliances, filename=f"appliances_{household.name.replace(' ', '_')}.xlsx")
