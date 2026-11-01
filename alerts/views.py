from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import EnergyAlert, EnergyAlertRule
from .services import evaluate_household_alerts, initialize_default_rules


@login_required
def alert_list(request):
    household = request.active_household
    if not household:
        return redirect('households:create')

    # Trigger rule evaluation on load
    evaluate_household_alerts(household)

    severity_filter = request.GET.get('severity')
    alerts = EnergyAlert.objects.filter(household=household, is_dismissed=False)

    if severity_filter:
        alerts = alerts.filter(severity=severity_filter)

    unread_count = alerts.filter(is_read=False).count()
    rules = household.alert_rules.all()

    return render(request, 'alerts/list.html', {
        'household': household,
        'alerts': alerts,
        'unread_count': unread_count,
        'rules': rules,
        'severity_filter': severity_filter,
    })


@login_required
def alert_mark_read(request, pk):
    alert = get_object_or_404(EnergyAlert, pk=pk)
    if not alert.household.user_has_permission(request.user, 'view'):
        return HttpResponseForbidden("Access Denied.")

    alert.is_read = True
    alert.save(update_fields=['is_read'])
    return redirect('alerts:list')


@login_required
def alert_dismiss(request, pk):
    alert = get_object_or_404(EnergyAlert, pk=pk)
    if not alert.household.user_has_permission(request.user, 'view'):
        return HttpResponseForbidden("Access Denied.")

    alert.is_dismissed = True
    alert.save(update_fields=['is_dismissed'])
    messages.info(request, "Alert dismissed.")
    return redirect('alerts:list')


@login_required
def alert_dismiss_all(request):
    household = request.active_household
    if household and request.method == 'POST':
        EnergyAlert.objects.filter(household=household, is_dismissed=False).update(is_dismissed=True, is_read=True)
        messages.info(request, "All alerts dismissed.")
    return redirect('alerts:list')


@login_required
def alert_rule_toggle(request, pk):
    rule = get_object_or_404(EnergyAlertRule, pk=pk)
    if not rule.household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        rule.is_enabled = not rule.is_enabled
        rule.save(update_fields=['is_enabled'])
        state = "enabled" if rule.is_enabled else "disabled"
        messages.info(request, f"Alert rule '{rule.get_rule_type_display()}' {state}.")

    return redirect('alerts:list')
