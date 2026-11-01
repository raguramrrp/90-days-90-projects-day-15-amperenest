from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from decimal import Decimal
from .models import Appliance
from .forms import ApplianceForm


@login_required
def appliance_list(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    appliances = household.appliances.all().order_by('-is_active', '-rated_power_watts')
    total_monthly_kwh = sum(a.monthly_consumption_kwh for a in appliances if a.is_active)
    total_est_cost = sum(a.estimate_monthly_cost() for a in appliances if a.is_active)

    return render(request, 'appliances/list.html', {
        'household': household,
        'appliances': appliances,
        'total_monthly_kwh': total_monthly_kwh,
        'total_est_cost': total_est_cost,
    })


@login_required
def appliance_create(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    if not household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        form = ApplianceForm(request.POST)
        if form.is_valid():
            appliance = form.save(commit=False)
            appliance.household = household
            appliance.save()
            messages.success(request, f"Appliance '{appliance.name}' added to household inventory.")
            return redirect('appliances:list')
    else:
        form = ApplianceForm()

    return render(request, 'appliances/form.html', {'form': form, 'title': 'Add Household Appliance', 'household': household})


@login_required
def appliance_edit(request, pk):
    appliance = get_object_or_404(Appliance, pk=pk)
    if not appliance.household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied.")

    household = appliance.household
    if request.method == 'POST':
        form = ApplianceForm(request.POST, instance=appliance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Appliance '{appliance.name}' updated.")
            return redirect('appliances:list')
    else:
        form = ApplianceForm(instance=appliance)

    return render(request, 'appliances/form.html', {'form': form, 'title': f"Edit {appliance.name}", 'appliance': appliance})


@login_required
def appliance_delete(request, pk):
    appliance = get_object_or_404(Appliance, pk=pk)
    if not appliance.household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        name = appliance.name
        appliance.delete()
        messages.info(request, f"Appliance '{name}' removed from inventory.")
        return redirect('appliances:list')

    return render(request, 'appliances/confirm_delete.html', {'appliance': appliance})


@login_required
def appliance_insights(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    appliances = household.appliances.filter(is_active=True).order_by('-rated_power_watts')
    total_kwh = sum(a.monthly_consumption_kwh for a in appliances)

    # Compute breakdown with percentages
    breakdown = []
    for a in appliances:
        share = ((a.monthly_consumption_kwh / total_kwh) * Decimal('100.0')) if total_kwh > 0 else Decimal('0.0')
        breakdown.append({
            'appliance': a,
            'monthly_kwh': a.monthly_consumption_kwh,
            'monthly_cost': a.estimate_monthly_cost(),
            'share_pct': share.quantize(Decimal('0.1')),
        })

    breakdown.sort(key=lambda x: x['monthly_kwh'], reverse=True)

    return render(request, 'appliances/insights.html', {
        'household': household,
        'breakdown': breakdown,
        'total_kwh': total_kwh,
        'total_cost': sum(b['monthly_cost'] for b in breakdown),
    })
