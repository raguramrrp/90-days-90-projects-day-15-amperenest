from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Household, HouseholdMember
from .forms import HouseholdForm, HouseholdMemberForm
from .middleware import models_q_user_households


@login_required
def household_list(request):
    households = Household.objects.filter(
        models_q_user_households(request.user),
        is_archived=False
    )
    return render(request, 'households/list.html', {
        'households': households,
    })


@login_required
def household_create(request):
    if request.method == 'POST':
        form = HouseholdForm(request.POST)
        if form.is_valid():
            household = form.save(commit=False)
            household.created_by = request.user
            household.save()

            # Switch active household to new one
            request.session['active_household_id'] = household.id
            messages.success(request, f"Household '{household.name}' created and set as active.")
            return redirect('households:detail', pk=household.pk)
    else:
        form = HouseholdForm()

    return render(request, 'households/form.html', {'form': form, 'title': 'Add New Household Property'})


@login_required
def household_detail(request, pk):
    household = get_object_or_404(Household, pk=pk)
    if not household.user_has_permission(request.user, 'view'):
        return HttpResponseForbidden("Access Denied: You do not have permission to view this household.")

    members = household.memberships.select_related('user')
    meters = household.meters.all()
    appliances = household.appliances.all()
    member_form = HouseholdMemberForm()

    return render(request, 'households/detail.html', {
        'household': household,
        'members': members,
        'meters': meters,
        'appliances': appliances,
        'member_form': member_form,
    })


@login_required
def household_edit(request, pk):
    household = get_object_or_404(Household, pk=pk)
    if not household.user_has_permission(request.user, 'manage_budget'):
        return HttpResponseForbidden("Access Denied: Only owners and admins can edit household details.")

    if request.method == 'POST':
        form = HouseholdForm(request.POST, instance=household)
        if form.is_valid():
            form.save()
            messages.success(request, f"Household '{household.name}' updated successfully.")
            return redirect('households:detail', pk=household.pk)
    else:
        form = HouseholdForm(instance=household)

    return render(request, 'households/form.html', {'form': form, 'title': f"Edit {household.name}", 'household': household})


@login_required
def household_switch(request, pk):
    household = get_object_or_404(Household, pk=pk)
    if not household.user_has_permission(request.user, 'view'):
        messages.error(request, "Permission denied to switch to this household.")
        return redirect('core:dashboard')

    request.session['active_household_id'] = household.id
    messages.info(request, f"Active household switched to '{household.name}'.")
    next_url = request.GET.get('next')
    return redirect(next_url or 'core:dashboard')


@login_required
def member_add(request, pk):
    household = get_object_or_404(Household, pk=pk)
    if household.created_by != request.user:
        return HttpResponseForbidden("Access Denied: Only the household owner can add members.")

    if request.method == 'POST':
        form = HouseholdMemberForm(request.POST)
        if form.is_valid():
            target_user = form.clean_username()
            if target_user == request.user:
                messages.warning(request, "You are already the owner of this household.")
            elif HouseholdMember.objects.filter(household=household, user=target_user).exists():
                messages.warning(request, f"{target_user.username} is already a member.")
            else:
                member = form.save(commit=False)
                member.household = household
                member.user = target_user
                member.save()
                messages.success(request, f"Added {target_user.username} to {household.name} as {member.role}.")
        else:
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, e)

    return redirect('households:detail', pk=household.pk)


@login_required
def member_remove(request, pk, member_id):
    household = get_object_or_404(Household, pk=pk)
    if household.created_by != request.user:
        return HttpResponseForbidden("Access Denied.")

    member = get_object_or_404(HouseholdMember, pk=member_id, household=household)
    member_user = member.user.username
    member.delete()
    messages.info(request, f"Removed {member_user} from household.")
    return redirect('households:detail', pk=household.pk)
