from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import ElectricityMeter
from .forms import ElectricityMeterForm


@login_required
def meter_list(request):
    household = request.active_household
    if not household:
        messages.warning(request, "Please create or select a household first.")
        return redirect('households:create')

    meters = household.meters.all().select_related('tariff_plan')
    return render(request, 'meters/list.html', {
        'household': household,
        'meters': meters,
    })


@login_required
def meter_create(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    if not household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        form = ElectricityMeterForm(request.POST)
        if form.is_valid():
            meter = form.save(commit=False)
            meter.household = household
            meter.save()
            messages.success(request, f"Meter '{meter.meter_name}' registered successfully.")
            return redirect('meters:detail', pk=meter.pk)
    else:
        # Prepopulate provider and load from household
        form = ElectricityMeterForm(initial={
            'electricity_provider': 'TANGEDCO / TNPDCL',
            'sanctioned_load_kw': household.sanctioned_load_kw,
            'reading_unit': 'kWh',
            'dial_digits': 5,
        })

    return render(request, 'meters/form.html', {'form': form, 'title': 'Register New Electricity Meter', 'household': household})


@login_required
def meter_detail(request, pk):
    meter = get_object_or_404(ElectricityMeter, pk=pk)
    if not meter.household.user_has_permission(request.user, 'view'):
        return HttpResponseForbidden("Access Denied.")

    readings = meter.readings.all().order_by('-reading_date')[:20]
    bills = meter.bills.all().order_by('-billing_period_end')[:10]

    return render(request, 'meters/detail.html', {
        'meter': meter,
        'readings': readings,
        'bills': bills,
    })


@login_required
def meter_edit(request, pk):
    meter = get_object_or_404(ElectricityMeter, pk=pk)
    if not meter.household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        form = ElectricityMeterForm(request.POST, instance=meter)
        if form.is_valid():
            form.save()
            messages.success(request, f"Meter '{meter.meter_name}' updated.")
            return redirect('meters:detail', pk=meter.pk)
    else:
        form = ElectricityMeterForm(instance=meter)

    return render(request, 'meters/form.html', {'form': form, 'title': f"Edit {meter.meter_name}", 'meter': meter})


@login_required
def meter_archive(request, pk):
    meter = get_object_or_404(ElectricityMeter, pk=pk)
    if not meter.household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        meter.meter_status = 'Archived' if meter.meter_status == 'Active' else 'Active'
        meter.save()
        status_label = "archived" if meter.meter_status == 'Archived' else "restored to active"
        messages.info(request, f"Meter '{meter.meter_name}' {status_label}.")
        return redirect('meters:list')

    return render(request, 'meters/confirm_archive.html', {'meter': meter})
