from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from .models import EnergyAlertRule, EnergyAlert
from meters.models import ElectricityMeter
from consumption.models import MeterReading
from billing.models import ElectricityBill
from consumption.services import get_billing_cycle_boundaries
from tariffs.services import get_tariff_for_date


def evaluate_household_alerts(household):
    """
    Evaluates enabled alert rules against real database records for the given household.
    Generates new non-duplicate alerts as appropriate.
    """
    today = timezone.localdate()
    generated_alerts = []

    # Get active rules or create defaults if none exist
    rules = household.alert_rules.filter(is_enabled=True)
    if not rules.exists():
        rules = initialize_default_rules(household)

    active_meters = household.meters.filter(meter_status='Active')

    for rule in rules:
        if rule.rule_type == 'high_daily_kwh':
            # Check latest reading consumption on each meter
            threshold = rule.threshold_value if rule.threshold_value > 0 else Decimal('15.00')
            recent_readings = MeterReading.objects.filter(
                meter__in=active_meters,
                reading_date__gte=today - timedelta(days=2),
                consumption_kwh__gt=threshold,
                is_flagged_inversion=False
            )
            for r in recent_readings:
                title = f"High Daily Consumption on {r.meter.meter_name}"
                msg = f"Reading of {r.consumption_kwh} kWh on {r.reading_date} exceeded your alert threshold of {threshold} kWh."
                alert = create_alert_if_not_exists(
                    household=household,
                    rule=rule,
                    alert_type='high_daily_kwh',
                    title=title,
                    message=msg,
                    severity='warning',
                    today=today
                )
                if alert:
                    generated_alerts.append(alert)

        elif rule.rule_type == 'unusual_spike_pct':
            threshold_pct = rule.threshold_value if rule.threshold_value > 0 else Decimal('50.00')
            for meter in active_meters:
                readings = list(MeterReading.objects.filter(
                    meter=meter,
                    reading_date__gte=today - timedelta(days=8),
                    is_flagged_inversion=False
                ).order_by('-reading_date')[:8])

                if len(readings) >= 3:
                    latest = readings[0]
                    prev_readings = readings[1:]
                    avg_prev = sum(r.consumption_kwh for r in prev_readings) / Decimal(len(prev_readings))
                    if avg_prev > Decimal('1.00'):
                        increase_pct = ((latest.consumption_kwh - avg_prev) / avg_prev) * Decimal('100.0')
                        if increase_pct >= threshold_pct:
                            title = f"Unusual Consumption Surge on {meter.meter_name}"
                            msg = f"Latest reading ({latest.consumption_kwh} kWh) is {increase_pct:.1f}% higher than your 7-day average ({avg_prev:.1f} kWh)."
                            alert = create_alert_if_not_exists(
                                household=household,
                                rule=rule,
                                alert_type='unusual_spike_pct',
                                title=title,
                                message=msg,
                                severity='warning',
                                today=today
                            )
                            if alert:
                                generated_alerts.append(alert)

        elif rule.rule_type == 'budget_threshold_pct':
            threshold_pct = rule.threshold_value if rule.threshold_value > 0 else Decimal('80.00')
            cycle_info = get_billing_cycle_boundaries(household)
            cycle_readings = MeterReading.objects.filter(
                meter__in=active_meters,
                reading_date__gte=cycle_info['cycle_start'],
                reading_date__lte=today,
                is_flagged_inversion=False
            )
            cycle_units = sum(r.consumption_kwh for r in cycle_readings)

            # Estimate cost so far
            primary_meter = active_meters.first()
            tariff = get_tariff_for_date(primary_meter, today)
            estimated_cost = Decimal('0.00')
            if tariff:
                calc = tariff.calculate_bill(cycle_units, household.sanctioned_load_kw)
                estimated_cost = calc['total_bill_amount']

            budget = household.monthly_budget_amount
            if budget > 0:
                utilization_pct = (estimated_cost / budget) * Decimal('100.0')
                if utilization_pct >= threshold_pct:
                    title = f"Monthly Budget Usage Reached {utilization_pct:.0f}%"
                    msg = f"Current cycle estimated spend is ₹{estimated_cost:,.2f}, reaching {utilization_pct:.1f}% of your ₹{budget:,.2f} monthly budget with {cycle_info['days_remaining']} days remaining."
                    alert = create_alert_if_not_exists(
                        household=household,
                        rule=rule,
                        alert_type='budget_threshold_pct',
                        title=title,
                        message=msg,
                        severity='warning' if utilization_pct < 100 else 'danger',
                        today=today
                    )
                    if alert:
                        generated_alerts.append(alert)

        elif rule.rule_type == 'bill_due_soon':
            days_threshold = int(rule.threshold_value) if rule.threshold_value > 0 else 3
            due_soon_bills = ElectricityBill.objects.filter(
                meter__household=household,
                payment_status='Pending',
                due_date__isnull=False,
                due_date__gte=today,
                due_date__lte=today + timedelta(days=days_threshold)
            )
            for bill in due_soon_bills:
                days_left = (bill.due_date - today).days
                title = f"Electricity Bill Due in {days_left} Days"
                msg = f"Bill #{bill.bill_number or bill.id} for {bill.meter.meter_name} (₹{bill.total_bill_amount:,.2f}) is due on {bill.due_date}."
                alert = create_alert_if_not_exists(
                    household=household,
                    rule=rule,
                    alert_type='bill_due_soon',
                    title=title,
                    message=msg,
                    severity='warning',
                    today=today
                )
                if alert:
                    generated_alerts.append(alert)

        elif rule.rule_type == 'bill_overdue':
            overdue_bills = ElectricityBill.objects.filter(
                meter__household=household,
                payment_status__in=['Pending', 'Overdue'],
                due_date__isnull=False,
                due_date__lt=today
            )
            for bill in overdue_bills:
                bill.payment_status = 'Overdue'
                bill.save(update_fields=['payment_status'])
                days_over = (today - bill.due_date).days
                title = f"Electricity Bill Overdue by {days_over} Days"
                msg = f"Bill #{bill.bill_number or bill.id} (₹{bill.total_bill_amount:,.2f}) was due on {bill.due_date} and is currently overdue."
                alert = create_alert_if_not_exists(
                    household=household,
                    rule=rule,
                    alert_type='bill_overdue',
                    title=title,
                    message=msg,
                    severity='danger',
                    today=today
                )
                if alert:
                    generated_alerts.append(alert)

        elif rule.rule_type == 'missing_reading_days':
            max_days = int(rule.threshold_value) if rule.threshold_value > 0 else 5
            for meter in active_meters:
                latest = meter.latest_reading
                if latest:
                    gap_days = (today - latest.reading_date).days
                    if gap_days > max_days:
                        title = f"No Reading Recorded for {gap_days} Days"
                        msg = f"Meter '{meter.meter_name}' has not had a reading entered since {latest.reading_date}. Record a reading to keep forecasts accurate."
                        alert = create_alert_if_not_exists(
                            household=household,
                            rule=rule,
                            alert_type='missing_reading_days',
                            title=title,
                            message=msg,
                            severity='info',
                            today=today
                        )
                        if alert:
                            generated_alerts.append(alert)

        elif rule.rule_type == 'inconsistent_reading':
            inversions = MeterReading.objects.filter(
                meter__in=active_meters,
                is_flagged_inversion=True,
                reading_date__gte=today - timedelta(days=7)
            )
            for inv in inversions:
                title = f"Inconsistent Meter Reading on {inv.meter.meter_name}"
                msg = f"The reading of {inv.reading_value} on {inv.reading_date} is lower than the previous reading. If the meter was replaced, mark it as reset."
                alert = create_alert_if_not_exists(
                    household=household,
                    rule=rule,
                    alert_type='inconsistent_reading',
                    title=title,
                    message=msg,
                    severity='warning',
                    today=today
                )
                if alert:
                    generated_alerts.append(alert)

    return generated_alerts


def create_alert_if_not_exists(household, rule, alert_type, title, message, severity, today):
    """Prevents duplicate active alerts created on the same day."""
    existing = EnergyAlert.objects.filter(
        household=household,
        alert_type=alert_type,
        title=title,
        created_at__date=today,
        is_dismissed=False
    ).first()

    if not existing:
        return EnergyAlert.objects.create(
            household=household,
            alert_rule=rule,
            alert_type=alert_type,
            title=title,
            message=message,
            severity=severity
        )
    return None


def initialize_default_rules(household):
    """Creates recommended default alert rules for a new household."""
    defaults = [
        ('high_daily_kwh', Decimal('15.00')),
        ('unusual_spike_pct', Decimal('50.00')),
        ('budget_threshold_pct', Decimal('80.00')),
        ('projected_overrun', Decimal('0.00')),
        ('bill_due_soon', Decimal('3.00')),
        ('bill_overdue', Decimal('0.00')),
        ('missing_reading_days', Decimal('5.00')),
        ('inconsistent_reading', Decimal('0.00')),
    ]
    created_rules = []
    for r_type, thresh in defaults:
        rule, _ = EnergyAlertRule.objects.get_or_create(
            household=household,
            rule_type=r_type,
            defaults={'threshold_value': thresh, 'is_enabled': True}
        )
        created_rules.append(rule)
    return household.alert_rules.filter(is_enabled=True)
