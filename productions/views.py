from django.contrib import messages
from django.db.models import Sum, F
from django.shortcuts import get_object_or_404, redirect, render

from accounts.access import (
    is_admin,
    is_farmer,
    is_manager,
    roles_required,
    user_cooperative,
    user_member,
)
from accounts.models import UserProfile
from cooperatives.models import Cooperative

from .forms import ProductionForm, FarmerProductionForm
from .models import Production


def _selected_cooperative(request):
    if is_manager(request.user):
        return user_cooperative(request.user)
    cooperative_id = request.GET.get('cooperative')
    if cooperative_id:
        return Cooperative.objects.filter(pk=cooperative_id).first()
    return user_cooperative(request.user)


@roles_required(
    UserProfile.Role.ADMIN,
    UserProfile.Role.COOPERATIVE_MANAGER,
    UserProfile.Role.FARMER,
)
def production_list(request):
    user = request.user
    selected_cooperative = request.GET.get('cooperative', '').strip()
    if is_admin(user):
        productions = Production.objects.select_related('member', 'product', 'member__cooperative')
        if selected_cooperative:
            productions = productions.filter(
                member__cooperative_id=selected_cooperative
            )
    elif is_manager(user):
        selected_cooperative = str(
            getattr(user_cooperative(user), 'pk', '')
        )
        productions = Production.objects.filter(
            member__cooperative=user_cooperative(user)
        ).select_related('member', 'product', 'member__cooperative')
    else:
        member = user_member(user)
        if member:
            productions = Production.objects.filter(member=member).select_related('member', 'product')
        else:
            productions = Production.objects.none()

    return render(request, 'productions/production_list.html', {
        'productions': productions,
        'cooperatives': Cooperative.objects.all(),
        'selected_cooperative': selected_cooperative,
        'is_admin_view': is_admin(user),
        'can_manage': not is_farmer(user),
    })

@roles_required(
    UserProfile.Role.ADMIN,
    UserProfile.Role.COOPERATIVE_MANAGER,
    UserProfile.Role.FARMER,
)
def production_create(request):
    user = request.user
    can_manage = is_admin(user) or is_manager(user)
    member = user_member(user)
    cooperative = _selected_cooperative(request)
    if is_farmer(user) and member:
        cooperative = member.cooperative

    if request.method == 'POST':
        if can_manage:
            form = ProductionForm(request.POST, cooperative=cooperative)
        else:
            form = FarmerProductionForm(request.POST, cooperative=cooperative)
            
        if form.is_valid():
            production = form.save(commit=False)
            if not can_manage:
                if not member:
                    messages.error(request, "Impossible de declarer une recolte : aucun profil membre trouve pour votre compte.")
                    return redirect('productions:list')
                production.member = member
            
            production.save()
            
            product = production.product
            product.quantity_available = F('quantity_available') + production.quantity
            product.save(update_fields=['quantity_available'])
            
            messages.success(request, 'Recolte declaree avec succes.')
            return redirect('productions:list')
    else:
        if can_manage:
            form = ProductionForm(cooperative=cooperative)
        else:
            form = FarmerProductionForm(cooperative=cooperative)

    return render(request, 'productions/production_form.html', {
        'form': form,
        'title': 'Declarer une recolte',
        'submit_label': 'Declarer',
    })

@roles_required(
    UserProfile.Role.ADMIN,
    UserProfile.Role.COOPERATIVE_MANAGER,
    UserProfile.Role.FARMER,
)
def production_update(request, pk):
    user = request.user
    can_manage = is_admin(user) or is_manager(user)
    productions = Production.objects.all()
    member = user_member(user)
    if is_manager(user):
        productions = productions.filter(member__cooperative=user_cooperative(user))
    elif is_farmer(user):
        productions = productions.filter(member=member)
    production = get_object_or_404(productions, pk=pk)

    old_quantity = production.quantity
    old_product = production.product

    if request.method == 'POST':
        if can_manage:
            form = ProductionForm(request.POST, instance=production, cooperative=production.member.cooperative)
        else:
            form = FarmerProductionForm(request.POST, instance=production, cooperative=production.member.cooperative)
            
        if form.is_valid():
            production = form.save()
            
            old_product.quantity_available = F('quantity_available') - old_quantity
            old_product.save(update_fields=['quantity_available'])
            
            new_product = production.product
            new_product.quantity_available = F('quantity_available') + production.quantity
            new_product.save(update_fields=['quantity_available'])
            
            messages.success(request, 'Production modifiee avec succes.')
            return redirect('productions:list')
    else:
        if can_manage:
            form = ProductionForm(instance=production, cooperative=production.member.cooperative)
        else:
            form = FarmerProductionForm(instance=production, cooperative=production.member.cooperative)

    return render(request, 'productions/production_form.html', {
        'form': form,
        'title': 'Modifier la production',
        'submit_label': 'Enregistrer',
        'production': production,
    })

@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.COOPERATIVE_MANAGER)
def production_stats(request):
    productions = Production.objects.all()
    if is_manager(request.user):
        productions = productions.filter(
            member__cooperative=user_cooperative(request.user)
        )
    totals = productions.aggregate(
        total_qty=Sum('quantity'),
        total_val=Sum('estimated_price')
    )
    
    by_product = productions.values(
        'product__name',
        'product__unit',
    ).annotate(
        qty=Sum('quantity'),
        val=Sum('estimated_price')
    ).order_by('-qty')
    
    return render(request, 'productions/production_stats.html', {
        'total_qty': totals['total_qty'] or 0,
        'total_val': totals['total_val'] or 0,
        'by_product': by_product,
    })
