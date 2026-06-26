from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Prefetch, Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.access import is_admin, is_manager, roles_required, user_cooperative
from accounts.models import UserProfile

from .forms import CooperativeForm
from .models import Cooperative


def _assign_manager(cooperative, manager):
    UserProfile.objects.filter(
        role=UserProfile.Role.COOPERATIVE_MANAGER,
        cooperative=cooperative,
    ).exclude(user=manager).update(
        role=UserProfile.Role.BUYER,
        cooperative=None,
    )
    profile = manager.profile
    profile.role = UserProfile.Role.COOPERATIVE_MANAGER
    profile.cooperative = cooperative
    profile.save(update_fields=['role', 'cooperative', 'updated_at'])


@roles_required(UserProfile.Role.ADMIN)
def cooperative_list(request):
    manager_profiles = UserProfile.objects.filter(
        role=UserProfile.Role.COOPERATIVE_MANAGER
    ).select_related('user')
    cooperatives = Cooperative.objects.annotate(
        member_count=Count('members', distinct=True),
        product_count=Count('products', distinct=True),
    ).prefetch_related(
        Prefetch(
            'user_profiles',
            queryset=manager_profiles,
            to_attr='manager_profiles',
        )
    )
    return render(request, 'cooperatives/cooperative_list.html', {
        'cooperatives': cooperatives,
        'can_manage': True,
    })


@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.COOPERATIVE_MANAGER)
def cooperative_detail(request, pk):
    cooperatives = Cooperative.objects.all()
    if is_manager(request.user):
        cooperatives = cooperatives.filter(
            pk=getattr(user_cooperative(request.user), 'pk', None)
        )
    cooperative = get_object_or_404(cooperatives, pk=pk)
    manager_profile = cooperative.user_profiles.filter(
        role=UserProfile.Role.COOPERATIVE_MANAGER
    ).select_related('user').first()
    products = cooperative.products.all()
    return render(request, 'cooperatives/cooperative_detail.html', {
        'cooperative': cooperative,
        'can_manage': True,
        'can_delete': is_admin(request.user),
        'manager': manager_profile.user if manager_profile else None,
        'member_count': cooperative.members.count(),
        'product_count': products.count(),
        'production_total': cooperative.members.aggregate(
            total=Sum('productions__quantity')
        )['total'] or 0,
        'stock_total': products.aggregate(
            total=Sum('quantity_available')
        )['total'] or 0,
    })


@roles_required(UserProfile.Role.ADMIN)
def cooperative_create(request):
    if request.method == 'POST':
        form = CooperativeForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                cooperative = form.save()
                _assign_manager(cooperative, form.cleaned_data['manager'])
            messages.success(
                request,
                'Cooperative creee et responsable affecte avec succes.',
            )
            return redirect(cooperative)
    else:
        form = CooperativeForm()
    return render(request, 'cooperatives/cooperative_form.html', {
        'form': form,
        'title': 'Creer une cooperative',
        'submit_label': 'Creer',
    })


@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.COOPERATIVE_MANAGER)
def cooperative_update(request, pk):
    cooperatives = Cooperative.objects.all()
    if is_manager(request.user):
        cooperatives = cooperatives.filter(
            pk=getattr(user_cooperative(request.user), 'pk', None)
        )
    cooperative = get_object_or_404(cooperatives, pk=pk)
    allow_manager_assignment = is_admin(request.user)
    if request.method == 'POST':
        form = CooperativeForm(
            request.POST,
            request.FILES,
            instance=cooperative,
            allow_manager_assignment=allow_manager_assignment,
        )
        if form.is_valid():
            with transaction.atomic():
                cooperative = form.save()
                if allow_manager_assignment:
                    _assign_manager(
                        cooperative,
                        form.cleaned_data['manager'],
                    )
            messages.success(request, 'Cooperative modifiee avec succes.')
            return redirect(cooperative)
    else:
        form = CooperativeForm(
            instance=cooperative,
            allow_manager_assignment=allow_manager_assignment,
        )
    return render(request, 'cooperatives/cooperative_form.html', {
        'form': form,
        'title': 'Modifier la cooperative',
        'submit_label': 'Enregistrer',
        'cooperative': cooperative,
    })


@roles_required(UserProfile.Role.ADMIN)
def cooperative_delete(request, pk):
    cooperative = get_object_or_404(Cooperative, pk=pk)
    if request.method == 'POST':
        cooperative.delete()
        messages.success(request, 'Cooperative supprimee avec succes.')
        return redirect('cooperatives:list')
    return render(request, 'cooperatives/cooperative_confirm_delete.html', {
        'cooperative': cooperative,
    })
