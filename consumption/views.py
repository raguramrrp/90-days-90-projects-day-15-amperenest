from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import MeterReading, ImportHistory
from .forms import MeterReadingForm, DirectConsumptionForm, ReadingImportForm
from .services import import_readings_from_file, get_household_consumption_stats, get_billing_cycle_boundaries
from meters.models import ElectricityMeter
from alerts.services import evaluate_household_alerts


@login_required
def readings_list(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    meters = household.meters.filter(meter_status='Active')
    selected_meter_id = request.GET.get('meter')

    readings = MeterReading.objects.filter(meter__household=household).select_related('meter')

    if selected_meter_id:
        readings = readings.filter(meter_id=selected_meter_id)

    # Date range filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        readings = readings.filter(reading_date__gte=start_date)
    if end_date:
        readings = readings.filter(reading_date__lte=end_date)

    paginator = Paginator(readings.order_by('-reading_date', '-id'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate summary metrics
    stats = get_household_consumption_stats(household, days=30)
    cycle = get_billing_cycle_boundaries(household)

    return render(request, 'consumption/readings_list.html', {
        'household': household,
        'meters': meters,
        'selected_meter_id': selected_meter_id,
        'page_obj': page_obj,
        'stats': stats,
        'cycle': cycle,
        'start_date': start_date,
        'end_date': end_date,
    })


@login_required
def reading_create(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    if not household.user_has_permission(request.user, 'edit_reading'):
        return HttpResponseForbidden("Access Denied.")

    method = request.GET.get('method', 'cumulative')

    if request.method == 'POST':
        if method == 'direct':
            form = DirectConsumptionForm(request.POST, household=household)
            if form.is_valid():
                reading = form.save(commit=False)
                reading.reading_type = 'direct'
                reading.reading_source = 'Manual Entry'
                reading.reading_value = reading.consumption_kwh  # For direct entries
                reading.recorded_by = request.user
                reading.save()
                evaluate_household_alerts(household)
                messages.success(request, f"Direct consumption of {reading.consumption_kwh} kWh recorded on {reading.reading_date}.")
                return redirect('consumption:list')
        else:
            form = MeterReadingForm(request.POST, request.FILES, household=household)
            if form.is_valid():
                reading = form.save(commit=False)
                reading.recorded_by = request.user
                reading.save()
                evaluate_household_alerts(household)
                if reading.is_flagged_inversion:
                    messages.warning(request, f"Warning: Dial reading ({reading.reading_value}) is lower than the previous reading. Flagged as possible inversion.")
                else:
                    messages.success(request, f"Reading saved! Computed consumption: +{reading.consumption_kwh} kWh.")
                return redirect('consumption:list')
    else:
        meter_id = request.GET.get('meter')
        initial_data = {}
        if meter_id:
            initial_data['meter'] = meter_id
        if method == 'direct':
            form = DirectConsumptionForm(initial=initial_data, household=household)
        else:
            form = MeterReadingForm(initial=initial_data, household=household)

    return render(request, 'consumption/reading_form.html', {
        'form': form,
        'method': method,
        'title': 'Record Electricity Reading',
        'household': household
    })


@login_required
def reading_edit(request, pk):
    reading = get_object_or_404(MeterReading, pk=pk)
    if not reading.meter.household.user_has_permission(request.user, 'edit_reading'):
        return HttpResponseForbidden("Access Denied.")

    household = reading.meter.household

    if request.method == 'POST':
        form = MeterReadingForm(request.POST, request.FILES, instance=reading, household=household)
        if form.is_valid():
            reading = form.save()
            evaluate_household_alerts(household)
            messages.success(request, f"Reading on {reading.reading_date} updated.")
            return redirect('consumption:list')
    else:
        form = MeterReadingForm(instance=reading, household=household)

    return render(request, 'consumption/reading_form.html', {
        'form': form,
        'reading': reading,
        'title': f"Edit Reading - {reading.meter.meter_name}",
        'household': household
    })


@login_required
def reading_delete(request, pk):
    reading = get_object_or_404(MeterReading, pk=pk)
    if not reading.meter.household.user_has_permission(request.user, 'edit_reading'):
        return HttpResponseForbidden("Access Denied.")

    household = reading.meter.household
    if request.method == 'POST':
        date_str = reading.reading_date
        reading.delete()
        evaluate_household_alerts(household)
        messages.info(request, f"Reading for {date_str} deleted with cascading recalculation.")
        return redirect('consumption:list')

    return render(request, 'consumption/confirm_delete.html', {'reading': reading})


@login_required
def consumption_history(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    from analytics.services import get_dashboard_chart_data
    chart_data = get_dashboard_chart_data(household)

    return render(request, 'consumption/history.html', {
        'household': household,
        'chart_data': chart_data,
    })


@login_required
def readings_import(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    if not household.user_has_permission(request.user, 'edit_reading'):
        return HttpResponseForbidden("Access Denied.")

    import_result = None
    if request.method == 'POST':
        form = ReadingImportForm(request.POST, request.FILES, household=household)
        if form.is_valid():
            f = request.FILES['import_file']
            meter = form.cleaned_data.get('meter')
            meter_id = meter.id if meter else None

            res = import_readings_from_file(
                file_obj=f,
                household=household,
                meter_id=meter_id,
                user=request.user
            )
            import_result = res
            if res.get('success'):
                evaluate_household_alerts(household)
                messages.success(request, f"Successfully imported {res['imported']} readings ({res['failed']} failed).")
            else:
                messages.error(request, f"Import error: {res.get('error', 'Validation failed')}")
    else:
        form = ReadingImportForm(household=household)

    history = ImportHistory.objects.filter(household=household).order_by('-imported_at')[:10]

    return render(request, 'consumption/import.html', {
        'form': form,
        'household': household,
        'import_result': import_result,
        'history': history,
    })
