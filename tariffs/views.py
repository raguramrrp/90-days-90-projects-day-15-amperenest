from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TariffPlan, TariffSlab, TariffCharge, TariffHistory
from .forms import TariffPlanForm, TariffSlabForm, TariffChargeForm


@login_required
def tariff_list(request):
    tariffs = TariffPlan.objects.all().prefetch_related('slabs', 'additional_charges')
    return render(request, 'tariffs/list.html', {
        'tariffs': tariffs,
    })


@login_required
def tariff_detail(request, pk):
    tariff = get_object_or_404(TariffPlan, pk=pk)
    slabs = tariff.slabs.all().order_by('slab_order')
    charges = tariff.additional_charges.all()
    history = tariff.change_history.all()[:10]

    slab_form = TariffSlabForm()
    charge_form = TariffChargeForm()

    # Sample calculation for preview (e.g. 250 units preview)
    preview_calc = tariff.calculate_bill(units_consumed=250, sanctioned_load_kw=3.0)

    return render(request, 'tariffs/detail.html', {
        'tariff': tariff,
        'slabs': slabs,
        'charges': charges,
        'history': history,
        'slab_form': slab_form,
        'charge_form': charge_form,
        'preview_calc': preview_calc,
    })


@login_required
def tariff_create(request):
    if request.method == 'POST':
        form = TariffPlanForm(request.POST)
        if form.is_valid():
            tariff = form.save(commit=False)
            tariff.created_by = request.user
            tariff.save()
            messages.success(request, f"Tariff plan '{tariff.name}' created.")
            return redirect('tariffs:detail', pk=tariff.pk)
    else:
        form = TariffPlanForm()

    return render(request, 'tariffs/form.html', {'form': form, 'title': 'Create Electricity Tariff Schedule'})


@login_required
def tariff_edit(request, pk):
    tariff = get_object_or_404(TariffPlan, pk=pk)
    if request.method == 'POST':
        form = TariffPlanForm(request.POST, instance=tariff)
        if form.is_valid():
            form.save()
            TariffHistory.objects.create(
                tariff_plan=tariff,
                modified_by=request.user,
                change_summary=f"Updated tariff settings for {tariff.name}"
            )
            messages.success(request, f"Tariff schedule '{tariff.name}' updated.")
            return redirect('tariffs:detail', pk=tariff.pk)
    else:
        form = TariffPlanForm(instance=tariff)

    return render(request, 'tariffs/form.html', {'form': form, 'title': f"Edit {tariff.name}", 'tariff': tariff})


@login_required
def tariff_slab_add(request, pk):
    tariff = get_object_or_404(TariffPlan, pk=pk)
    if request.method == 'POST':
        form = TariffSlabForm(request.POST)
        if form.is_valid():
            slab = form.save(commit=False)
            slab.tariff_plan = tariff
            slab.save()
            messages.success(request, f"Added Slab {slab.slab_order} ({slab.slab_min} to {slab.slab_max} kWh @ ₹{slab.rate_per_kwh}).")
        else:
            messages.error(request, "Failed to add slab. Please check numeric values.")
    return redirect('tariffs:detail', pk=tariff.pk)


@login_required
def tariff_slab_delete(request, pk, slab_id):
    tariff = get_object_or_404(TariffPlan, pk=pk)
    slab = get_object_or_404(TariffSlab, pk=slab_id, tariff_plan=tariff)
    slab.delete()
    messages.info(request, "Slab deleted.")
    return redirect('tariffs:detail', pk=tariff.pk)


@login_required
def tariff_charge_add(request, pk):
    tariff = get_object_or_404(TariffPlan, pk=pk)
    if request.method == 'POST':
        form = TariffChargeForm(request.POST)
        if form.is_valid():
            charge = form.save(commit=False)
            charge.tariff_plan = tariff
            charge.save()
            messages.success(request, f"Added charge: {charge.name}.")
    return redirect('tariffs:detail', pk=tariff.pk)
