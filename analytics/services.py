from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.db.models import Sum
from consumption.models import MeterReading
from consumption.services import get_billing_cycle_boundaries
from tariffs.services import get_tariff_for_date
from appliances.models import Appliance
from budgets.models import EnergyBudget
from .models import ForecastRecord


def generate_billing_cycle_forecast(household, meter=None):
    """
    Performs reliable statistical moving-average consumption forecasting for the current cycle.
    Handles insufficient data explicitly without fabricating predictions.
    """
    today = timezone.localdate()
    cycle_info = get_billing_cycle_boundaries(household, today)
    start_date = cycle_info['cycle_start']
    end_date = cycle_info['cycle_end']
    days_elapsed = cycle_info['days_elapsed']
    days_remaining = cycle_info['days_remaining']

    meters = [meter] if meter else household.meters.filter(meter_status='Active')

    readings = MeterReading.objects.filter(
        meter__in=meters,
        reading_date__gte=start_date,
        reading_date__lte=today,
        is_flagged_inversion=False
    ).order_by('reading_date')

    readings_count = readings.count()

    # Safeguard against insufficient data, falling back to 30-day baseline if cycle just started
    using_recent_baseline = False
    if readings_count < 2 or days_elapsed < 3:
        recent_readings = MeterReading.objects.filter(
            meter__in=meters,
            reading_date__gte=today - timedelta(days=30),
            reading_date__lte=today,
            is_flagged_inversion=False
        ).order_by('reading_date')

        if recent_readings.count() >= 3:
            using_recent_baseline = True
            total_recent = sum(r.consumption_kwh for r in recent_readings)
            earliest_date = recent_readings.first().reading_date
            num_baseline_days = max(1, (today - earliest_date).days + 1)
            daily_avg = (Decimal(str(total_recent)) / Decimal(str(num_baseline_days))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            current_kwh = sum(r.consumption_kwh for r in readings)
            projected_additional_kwh = (daily_avg * Decimal(str(days_remaining))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            projected_total_kwh = current_kwh + projected_additional_kwh
            confidence = Decimal('70.0')
        else:
            return {
                'has_sufficient_data': False,
                'message': f"Insufficient readings recorded ({readings_count} in current cycle). At least 2-3 readings are needed to project consumption accurately.",
                'current_consumed_kwh': sum(r.consumption_kwh for r in readings),
                'cycle_info': cycle_info,
                'projected_total_kwh': None,
                'projected_bill_amount': None,
                'daily_average_kwh': None,
                'confidence_score_pct': Decimal('0.0'),
            }
    else:
        current_kwh = sum(r.consumption_kwh for r in readings)
        daily_avg = (Decimal(str(current_kwh)) / Decimal(str(days_elapsed))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        projected_additional_kwh = (daily_avg * Decimal(str(days_remaining))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        projected_total_kwh = current_kwh + projected_additional_kwh
        cycle_pct = Decimal(str(days_elapsed)) / Decimal(str(cycle_info['total_cycle_days']))
        confidence = min(Decimal('95.0'), Decimal('50.0') + (cycle_pct * Decimal('45.0'))).quantize(Decimal('0.1'))

    # Calculate estimated bill for projected consumption
    primary_meter = meters[0] if meters else None
    tariff = get_tariff_for_date(primary_meter, today)
    projected_bill_amount = Decimal('0.00')
    if tariff:
        calc = tariff.calculate_bill(projected_total_kwh, household.sanctioned_load_kw)
        projected_bill_amount = calc['total_bill_amount']

    # Confidence score calculation based on days elapsed in cycle (e.g. 50% through cycle = ~80% confidence)
    cycle_pct = Decimal(str(days_elapsed)) / Decimal(str(cycle_info['total_cycle_days']))
    confidence = min(Decimal('95.0'), Decimal('50.0') + (cycle_pct * Decimal('45.0'))).quantize(Decimal('0.1'))

    return {
        'has_sufficient_data': True,
        'message': f"Projected based on {days_elapsed} days of recorded usage ({daily_avg} kWh/day average).",
        'cycle_info': cycle_info,
        'current_consumed_kwh': current_kwh,
        'projected_total_kwh': projected_total_kwh,
        'projected_bill_amount': projected_bill_amount,
        'daily_average_kwh': daily_avg,
        'confidence_score_pct': confidence,
        'tariff_used': tariff.name if tariff else 'Default',
    }


def generate_energy_insights(household):
    """
    Evaluates real usage patterns and generates actionable, prioritized recommendations.
    """
    today = timezone.localdate()
    insights = []

    # 1. High-consuming appliance detection
    appliances = household.appliances.filter(is_active=True)
    if appliances.exists():
        total_appliance_kwh = sum(a.monthly_consumption_kwh for a in appliances)
        top_appliance = max(appliances, key=lambda a: a.monthly_consumption_kwh)
        if total_appliance_kwh > 0:
            top_share = (top_appliance.monthly_consumption_kwh / total_appliance_kwh) * Decimal('100.0')
            if top_share >= Decimal('30.0'):
                insights.append({
                    'category': 'Appliance Efficiency',
                    'title': f"{top_appliance.name} Accounts for {top_share:.0f}% of Estimated Appliance Usage",
                    'description': f"Using {top_appliance.name} for {top_appliance.daily_operating_hours} hrs/day consumes an estimated {top_appliance.monthly_consumption_kwh:.1f} kWh/month (~₹{top_appliance.estimate_monthly_cost():,.0f}).",
                    'action': f"Reducing daily runtime by 1-2 hours or adjusting thermostat to 24°C could save up to ₹{top_appliance.estimate_monthly_cost() * Decimal('0.20'):,.0f} every month.",
                    'impact': 'High',
                    'severity': 'warning'
                })

    # 2. Week-over-week consumption trend
    meters = household.meters.filter(meter_status='Active')
    this_week = MeterReading.objects.filter(
        meter__in=meters,
        reading_date__gte=today - timedelta(days=7),
        reading_date__lte=today,
        is_flagged_inversion=False
    )
    last_week = MeterReading.objects.filter(
        meter__in=meters,
        reading_date__gte=today - timedelta(days=14),
        reading_date__lt=today - timedelta(days=7),
        is_flagged_inversion=False
    )

    this_week_kwh = sum(r.consumption_kwh for r in this_week)
    last_week_kwh = sum(r.consumption_kwh for r in last_week)

    if last_week_kwh > Decimal('5.00') and this_week_kwh > 0:
        pct_change = ((this_week_kwh - last_week_kwh) / last_week_kwh) * Decimal('100.0')
        if pct_change > Decimal('15.0'):
            insights.append({
                'category': 'Consumption Trend',
                'title': f"Weekly Electricity Usage Increased by {pct_change:.1f}%",
                'description': f"Your household consumed {this_week_kwh:.1f} kWh over the last 7 days compared to {last_week_kwh:.1f} kWh during the prior week.",
                'action': "Check if heavy loads (air conditioning, water heaters, water pumps) ran longer than usual.",
                'impact': 'Medium',
                'severity': 'warning'
            })
        elif pct_change < Decimal('-10.0'):
            insights.append({
                'category': 'Consumption Trend',
                'title': f"Excellent Progress: Usage Down by {abs(pct_change):.1f}%",
                'description': f"Your consumption dropped to {this_week_kwh:.1f} kWh this week from {last_week_kwh:.1f} kWh last week.",
                'action': "Keep up the current efficiency habits to stay well under your monthly budget.",
                'impact': 'Positive',
                'severity': 'info'
            })

    # 3. Budget pacing insight
    cycle_info = get_billing_cycle_boundaries(household, today)
    forecast = generate_billing_cycle_forecast(household)
    if forecast.get('has_sufficient_data') and forecast.get('projected_bill_amount'):
        projected = forecast['projected_bill_amount']
        budget = household.monthly_budget_amount
        if budget > 0:
            if projected > budget:
                overrun = projected - budget
                insights.append({
                    'category': 'Budget Projection',
                    'title': f"Projected Budget Overrun of ₹{overrun:,.2f}",
                    'description': f"At the current daily pace ({forecast['daily_average_kwh']} kWh/day), your end-of-cycle bill is estimated at ₹{projected:,.2f}, exceeding your ₹{budget:,.2f} budget.",
                    'action': f"Target a daily average under {(Decimal(str(budget)) / Decimal('30.0') / Decimal('5.5')):,.1f} kWh for the remaining {cycle_info['days_remaining']} days to stay within budget.",
                    'impact': 'High',
                    'severity': 'danger'
                })
            else:
                savings = budget - projected
                insights.append({
                    'category': 'Budget Projection',
                    'title': f"On Track: Estimated Surplus of ₹{savings:,.2f}",
                    'description': f"Projected bill of ₹{projected:,.2f} is well within your ₹{budget:,.2f} monthly budget.",
                    'action': "No urgent changes needed. Monitor readings weekly to maintain this trajectory.",
                    'impact': 'Positive',
                    'severity': 'info'
                })

    return insights


def get_dashboard_chart_data(household, meter=None):
    """
    Generates structured JSON data for Plotly charts on the analytics dashboard:
    1. Daily consumption history (last 30 days)
    2. Monthly consumption totals (last 6-12 months)
    3. Appliance breakdown (estimated monthly kWh)
    """
    today = timezone.localdate()
    meters = [meter] if meter else household.meters.filter(meter_status='Active')

    # 1. Daily trend (last 30 days)
    start_30 = today - timedelta(days=29)
    daily_readings = MeterReading.objects.filter(
        meter__in=meters,
        reading_date__gte=start_30,
        reading_date__lte=today,
        is_flagged_inversion=False
    ).order_by('reading_date')

    # Map dates to kWh
    daily_map = {}
    curr = start_30
    while curr <= today:
        daily_map[curr.strftime('%Y-%m-%d')] = 0.0
        curr += timedelta(days=1)

    for r in daily_readings:
        d_str = r.reading_date.strftime('%Y-%m-%d')
        daily_map[d_str] = daily_map.get(d_str, 0.0) + float(r.consumption_kwh)

    daily_labels = list(daily_map.keys())
    daily_values = [round(v, 2) for v in daily_map.values()]

    # 2. Monthly usage (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        m_date = today.replace(day=1) - timedelta(days=i * 28)
        m_start = m_date.replace(day=1)
        next_m = m_start.month + 1 if m_start.month < 12 else 1
        next_y = m_start.year if m_start.month < 12 else m_start.year + 1
        m_end = date(next_y, next_m, 1) - timedelta(days=1)

        m_readings = MeterReading.objects.filter(
            meter__in=meters,
            reading_date__gte=m_start,
            reading_date__lte=m_end,
            is_flagged_inversion=False
        )
        total_m_kwh = sum(r.consumption_kwh for r in m_readings)
        monthly_data.append({
            'month': m_start.strftime('%b %Y'),
            'kwh': float(round(total_m_kwh, 2))
        })

    # 3. Appliance distribution
    appliances = household.appliances.filter(is_active=True).order_by('-rated_power_watts')
    appliance_labels = [a.name for a in appliances]
    appliance_values = [float(a.monthly_consumption_kwh) for a in appliances]

    return {
        'daily_dates': daily_labels,
        'daily_kwh': daily_values,
        'monthly_labels': [m['month'] for m in monthly_data],
        'monthly_kwh': [m['kwh'] for m in monthly_data],
        'appliance_labels': appliance_labels,
        'appliance_kwh': appliance_values,
    }
