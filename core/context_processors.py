from alerts.models import EnergyAlert


def global_energy_context(request):
    """
    Context processor injecting active household, unread alert counts,
    and user preferences into all rendered templates.
    """
    active_household = getattr(request, 'active_household', None)
    accessible_households = getattr(request, 'accessible_households', [])

    unread_alerts_count = 0
    recent_alerts = []
    user_theme = 'light'
    currency_symbol = '₹'

    if request.user.is_authenticated:
        if hasattr(request.user, 'profile'):
            user_theme = request.user.profile.theme_preference
            currency_symbol = request.user.profile.currency_symbol

        if active_household:
            unread_alerts = EnergyAlert.objects.filter(
                household=active_household,
                is_read=False,
                is_dismissed=False
            )
            unread_alerts_count = unread_alerts.count()
            recent_alerts = unread_alerts[:5]

    return {
        'active_household': active_household,
        'accessible_households': accessible_households,
        'unread_alerts_count': unread_alerts_count,
        'recent_alerts': recent_alerts,
        'user_theme': user_theme,
        'currency_symbol': currency_symbol,
        'app_name': 'AmpereNest',
    }
