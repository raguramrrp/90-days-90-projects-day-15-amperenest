from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from decimal import Decimal
from .models import EnergyBudget, EnergyGoal
from .forms import EnergyBudgetForm, EnergyGoalForm
from consumption.services import get_billing_cycle_boundaries
from consumption.models import MeterReading
from tariffs.services import get_tariff_for_date


@login_required
def budget_dashboard(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    today = timezone.localdate()
    cycle_info = get_billing_cycle_boundaries(household, today)

    # Fetch or auto-create budget for current month
    budget, _ = EnergyBudget.objects.get_or_create(
        household=household,
        month=today.month,
        year=today.year,
        defaults={
            'monthly_budget_amount': household.monthly_budget_amount,
            'target_consumption_kwh': Decimal('250.00'),
            'daily_target_kwh': Decimal('8.33'),
        }
    )

    # Calculate actual spend and consumption so far in current cycle
    meters = household.meters.filter(meter_status='Active')
    readings = MeterReading.objects.filter(
        meter__in=meters,
        reading_date__gte=cycle_info['cycle_start'],
        reading_date__lte=today,
        is_flagged_inversion=False
    )
    cycle_kwh = sum(r.consumption_kwh for r in readings)

    primary_meter = meters.first()
    tariff = get_tariff_for_date(primary_meter, today)
    estimated_bill = Decimal('0.00')
    if tariff:
        calc = tariff.calculate_bill(cycle_kwh, household.sanctioned_load_kw)
        estimated_bill = calc['total_bill_amount']

    budget_amount = budget.monthly_budget_amount
    remaining_budget = max(Decimal('0.00'), budget_amount - estimated_bill)
    utilization_pct = ((estimated_bill / budget_amount) * Decimal('100.0')) if budget_amount > 0 else Decimal('0.0')

    # Projected overrun check
    from analytics.services import generate_billing_cycle_forecast
    forecast = generate_billing_cycle_forecast(household)

    goals = household.goals.all().order_by('status', '-target_date')

    return render(request, 'budgets/dashboard.html', {
        'household': household,
        'budget': budget,
        'cycle_info': cycle_info,
        'cycle_kwh': cycle_kwh,
        'estimated_bill': estimated_bill,
        'remaining_budget': remaining_budget,
        'utilization_pct': min(Decimal('100.0'), utilization_pct).quantize(Decimal('0.1')),
        'forecast': forecast,
        'goals': goals,
    })


@login_required
def budget_edit(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    if not household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied.")

    today = timezone.localdate()
    budget, _ = EnergyBudget.objects.get_or_create(
        household=household,
        month=today.month,
        year=today.year,
        defaults={
            'monthly_budget_amount': household.monthly_budget_amount,
            'target_consumption_kwh': Decimal('250.00'),
            'daily_target_kwh': Decimal('8.33'),
        }
    )

    if request.method == 'POST':
        form = EnergyBudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, "Monthly energy budget updated.")
            return redirect('budgets:dashboard')
    else:
        form = EnergyBudgetForm(instance=budget)

    return render(request, 'budgets/form.html', {'form': form, 'title': f"Configure Budget - {today.strftime('%B %Y')}"})


@login_required
def goal_create(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    if not household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        form = EnergyGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.household = household
            goal.save()
            messages.success(request, f"Energy goal '{goal.title}' created.")
            return redirect('budgets:dashboard')
    else:
        today = timezone.localdate()
        form = EnergyGoalForm(initial={
            'start_date': today,
            'target_date': today.replace(day=28) if today.month == 2 else today.replace(day=30),
            'status': 'In Progress'
        })

    return render(request, 'budgets/goal_form.html', {'form': form, 'title': 'Create Energy Efficiency Goal'})


@login_required
def goal_edit(request, pk):
    goal = get_object_or_404(EnergyGoal, pk=pk)
    if not goal.household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        form = EnergyGoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, f"Goal '{goal.title}' updated.")
            return redirect('budgets:dashboard')
    else:
        form = EnergyGoalForm(instance=goal)

    return render(request, 'budgets/goal_form.html', {'form': form, 'title': f"Edit Goal: {goal.title}"})


@login_required
def goal_delete(request, pk):
    goal = get_object_or_404(EnergyGoal, pk=pk)
    if not goal.household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        goal.delete()
        messages.info(request, "Goal deleted.")
        return redirect('budgets:dashboard')

    return render(request, 'budgets/confirm_delete_goal.html', {'goal': goal})
