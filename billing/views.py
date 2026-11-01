from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import ElectricityBill, BillLineItem
from .forms import ElectricityBillForm, BillCalculatorForm
from tariffs.models import TariffPlan
from alerts.services import evaluate_household_alerts


@login_required
def bill_list(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    meters = household.meters.all()
    bills = ElectricityBill.objects.filter(meter__in=meters).select_related('meter', 'tariff_plan')

    # Summary numbers
    pending_bills = bills.filter(payment_status__in=['Pending', 'Overdue'])
    total_due = sum(b.total_bill_amount for b in pending_bills)
    paid_count = bills.filter(payment_status='Paid').count()

    return render(request, 'billing/list.html', {
        'household': household,
        'bills': bills,
        'total_due': total_due,
        'pending_count': pending_bills.count(),
        'paid_count': paid_count,
    })


@login_required
def bill_detail(request, pk):
    bill = get_object_or_404(ElectricityBill, pk=pk)
    if not bill.meter.household.user_has_permission(request.user, 'view'):
        return HttpResponseForbidden("Access Denied.")

    line_items = bill.line_items.all()
    return render(request, 'billing/detail.html', {
        'bill': bill,
        'line_items': line_items,
    })


@login_required
def bill_create(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    if not household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        form = ElectricityBillForm(request.POST, request.FILES, household=household)
        if form.is_valid():
            bill = form.save()
            evaluate_household_alerts(household)
            messages.success(request, f"Bill #{bill.bill_number or bill.id} saved.")
            return redirect('billing:detail', pk=bill.pk)
    else:
        form = ElectricityBillForm(household=household)

    return render(request, 'billing/form.html', {'form': form, 'title': 'Record Actual Electricity Bill'})


@login_required
def bill_edit(request, pk):
    bill = get_object_or_404(ElectricityBill, pk=pk)
    if not bill.meter.household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied.")

    household = bill.meter.household
    if request.method == 'POST':
        form = ElectricityBillForm(request.POST, request.FILES, instance=bill, household=household)
        if form.is_valid():
            bill = form.save()
            evaluate_household_alerts(household)
            messages.success(request, f"Bill #{bill.bill_number or bill.id} updated.")
            return redirect('billing:detail', pk=bill.pk)
    else:
        form = ElectricityBillForm(instance=bill, household=household)

    return render(request, 'billing/form.html', {'form': form, 'title': f"Edit Bill #{bill.bill_number or bill.id}"})


@login_required
def bill_mark_paid(request, pk):
    bill = get_object_or_404(ElectricityBill, pk=pk)
    if not bill.meter.household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        bill.payment_status = 'Paid'
        bill.payment_date = timezone.localdate()
        bill.save()
        evaluate_household_alerts(bill.meter.household)
        messages.success(request, f"Bill #{bill.bill_number or bill.id} marked as Paid.")

    return redirect('billing:detail', pk=bill.pk)


@login_required
def bill_calculator(request):
    household = request.active_household
    calc_result = None

    if request.method == 'POST':
        form = BillCalculatorForm(request.POST, household=household)
        if form.is_valid():
            tariff = form.cleaned_data['tariff_plan']
            units = form.cleaned_data['units_consumed']
            load = form.cleaned_data['sanctioned_load_kw']
            calc_result = tariff.calculate_bill(units, load)
    else:
        initial_units = request.GET.get('units')
        form = BillCalculatorForm(household=household, initial={'units_consumed': initial_units} if initial_units else None)
        if initial_units:
            try:
                tariff = form.fields['tariff_plan'].initial or TariffPlan.objects.filter(is_active=True).first()
                if tariff:
                    calc_result = tariff.calculate_bill(float(initial_units), household.sanctioned_load_kw if household else 3.0)
            except Exception:
                pass

    return render(request, 'billing/calculator.html', {
        'form': form,
        'calc_result': calc_result,
        'household': household,
    })
