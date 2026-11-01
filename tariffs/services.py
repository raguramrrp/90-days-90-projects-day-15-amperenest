from decimal import Decimal
from datetime import date
from .models import TariffPlan, TariffSlab, TariffCharge


def get_tariff_for_date(meter, target_date=None):
    """
    Finds the active tariff plan for the meter on the given target date.
    Falls back to meter's assigned tariff or the active system template.
    """
    if target_date is None:
        target_date = date.today()

    if meter and meter.tariff_plan:
        plan = meter.tariff_plan
        # Check if plan was effective on target_date
        if plan.effective_from <= target_date and (plan.effective_to is None or plan.effective_to >= target_date):
            return plan

    # Check for another active tariff plan matching the meter's provider/category
    matching = TariffPlan.objects.filter(
        is_active=True,
        effective_from__lte=target_date
    ).filter(
        models_q_effective_to(target_date)
    )

    if meter:
        provider_match = matching.filter(provider__iexact=meter.electricity_provider).first()
        if provider_match:
            return provider_match

    return matching.first() or TariffPlan.objects.filter(is_active=True).first()


def models_q_effective_to(target_date):
    from django.db.models import Q
    return Q(effective_to__isnull=True) | Q(effective_to__gte=target_date)


def create_default_tamilnadu_tariff(user=None):
    """
    Initializes verified standard Tamil Nadu Domestic LT-1A bimonthly residential tariff structure.
    Telescopic slabs:
    - 0 to 100 kWh: First 100 units subsidized free (State Govt Subsidy)
    - 101 to 200 kWh: ₹4.50 / kWh
    - 201 to 400 kWh: ₹6.00 / kWh
    - 401 to 500 kWh: ₹8.00 / kWh
    - Above 500 kWh: ₹11.00 / kWh
    """
    existing = TariffPlan.objects.filter(name__icontains="TANGEDCO Domestic LT-1A").first()
    if existing:
        return existing

    plan = TariffPlan.objects.create(
        name="TANGEDCO Domestic LT-1A (Verified Bimonthly)",
        provider="TANGEDCO / TNPDCL",
        state="Tamil Nadu",
        country="India",
        consumer_category="Residential (Domestic LT-1A)",
        billing_frequency="Bimonthly",
        effective_from=date(2024, 7, 1),
        is_active=True,
        fixed_charge_type="none",
        fixed_charge_rate=Decimal('0.00'),
        electricity_duty_pct=Decimal('5.00'),
        free_units_per_cycle=100,
        subsidy_description="TN Govt Free 100 Units Bimonthly Domestic Subsidy",
        is_system_template=True,
        created_by=user,
        notes="Configurable residential slab schedule based on Tamil Nadu Electricity Regulatory Commission (TNERC) tariff revision."
    )

    # Create Slabs
    TariffSlab.objects.create(tariff_plan=plan, slab_order=1, slab_min=Decimal('0.00'), slab_max=Decimal('100.00'), rate_per_kwh=Decimal('4.50'))
    TariffSlab.objects.create(tariff_plan=plan, slab_order=2, slab_min=Decimal('100.00'), slab_max=Decimal('200.00'), rate_per_kwh=Decimal('4.50'))
    TariffSlab.objects.create(tariff_plan=plan, slab_order=3, slab_min=Decimal('200.00'), slab_max=Decimal('400.00'), rate_per_kwh=Decimal('6.00'))
    TariffSlab.objects.create(tariff_plan=plan, slab_order=4, slab_min=Decimal('400.00'), slab_max=Decimal('500.00'), rate_per_kwh=Decimal('8.00'))
    TariffSlab.objects.create(tariff_plan=plan, slab_order=5, slab_min=Decimal('500.00'), slab_max=None, rate_per_kwh=Decimal('11.00'))

    # Add FPPCA fuel surcharge charge
    TariffCharge.objects.create(
        tariff_plan=plan,
        name="Fuel & Power Purchase Cost Adjustment (FPPCA)",
        charge_type="per_kwh",
        charge_value=Decimal('0.25'),
        is_active=True
    )

    return plan
