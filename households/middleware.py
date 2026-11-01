from .models import Household


class HouseholdContextMiddleware:
    """
    Ensures request.active_household is populated for authenticated users,
    scoped strictly to households the user owns or is an authorized member of.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            accessible_households = Household.objects.filter(
                models_q_user_households(request.user)
            ).filter(is_archived=False)

            active_id = request.session.get('active_household_id')
            active_household = None

            if active_id:
                active_household = accessible_households.filter(id=active_id).first()

            if not active_household:
                # Fallback to user's default household from profile or first accessible
                if hasattr(request.user, 'profile') and request.user.profile.default_household:
                    default_h = request.user.profile.default_household
                    if accessible_households.filter(id=default_h.id).exists():
                        active_household = default_h

                if not active_household:
                    active_household = accessible_households.first()

                if active_household:
                    request.session['active_household_id'] = active_household.id

            request.active_household = active_household
            request.accessible_households = accessible_households
        else:
            request.active_household = None
            request.accessible_households = Household.objects.none()

        response = self.get_response(request)
        return response


def models_q_user_households(user):
    from django.db.models import Q
    return Q(created_by=user) | Q(memberships__user=user)
