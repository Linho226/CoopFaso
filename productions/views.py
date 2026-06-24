from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, F
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ProductionForm, FarmerProductionForm
from .models import Production
from members.models import Member

def is_manager_or_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    role = getattr(getattr(user, 'profile', None), 'role', None)
    return role in {'ADMIN', 'COOPERATIVE_MANAGER'}

@login_required
def production_list(request):
    user = request.user
    role = getattr(getattr(user, 'profile', None), 'role', None)
    
    if user.is_superuser or user.is_staff or role == 'ADMIN':
        productions = Production.objects.select_related('member', 'product', 'member__cooperative')
    elif role == 'COOPERATIVE_MANAGER':
        productions = Production.objects.select_related('member', 'product', 'member__cooperative')
    else:
        member = None
        profile = getattr(user, 'profile', None)
        if profile and profile.phone:
            member = Member.objects.filter(phone=profile.phone).first()
        if not member:
            member = Member.objects.filter(first_name=user.first_name, last_name=user.last_name).first()
            
        if member:
            productions = Production.objects.filter(member=member).select_related('member', 'product')
        else:
            productions = Production.objects.none()

    return render(request, 'productions/production_list.html', {
        'productions': productions,
        'can_manage': is_manager_or_admin(user),
    })

@login_required
def production_create(request):
    user = request.user
    role = getattr(getattr(user, 'profile', None), 'role', None)
    is_manager = user.is_superuser or user.is_staff or role in {'ADMIN', 'COOPERATIVE_MANAGER'}
    
    cooperative = None
    member = None
    profile = getattr(user, 'profile', None)
    if profile and profile.phone:
        member = Member.objects.filter(phone=profile.phone).first()
    if not member:
        member = Member.objects.filter(first_name=user.first_name, last_name=user.last_name).first()
    if member:
        cooperative = member.cooperative

    if request.method == 'POST':
        if is_manager:
            form = ProductionForm(request.POST, cooperative=cooperative)
        else:
            form = FarmerProductionForm(request.POST, cooperative=cooperative)
            
        if form.is_valid():
            production = form.save(commit=False)
            if not is_manager:
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
        if is_manager:
            form = ProductionForm(cooperative=cooperative)
        else:
            form = FarmerProductionForm(cooperative=cooperative)

    return render(request, 'productions/production_form.html', {
        'form': form,
        'title': 'Declarer une recolte',
        'submit_label': 'Declarer',
    })

@login_required
def production_update(request, pk):
    production = get_object_or_404(Production, pk=pk)
    user = request.user
    role = getattr(getattr(user, 'profile', None), 'role', None)
    is_manager = user.is_superuser or user.is_staff or role in {'ADMIN', 'COOPERATIVE_MANAGER'}
    
    member = None
    profile = getattr(user, 'profile', None)
    if profile and profile.phone:
        member = Member.objects.filter(phone=profile.phone).first()
    if not member:
        member = Member.objects.filter(first_name=user.first_name, last_name=user.last_name).first()

    if not is_manager and production.member != member:
        messages.error(request, "Vous n'avez pas la permission de modifier cette production.")
        return redirect('productions:list')

    old_quantity = production.quantity
    old_product = production.product

    if request.method == 'POST':
        if is_manager:
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
        if is_manager:
            form = ProductionForm(instance=production, cooperative=production.member.cooperative)
        else:
            form = FarmerProductionForm(instance=production, cooperative=production.member.cooperative)

    return render(request, 'productions/production_form.html', {
        'form': form,
        'title': 'Modifier la production',
        'submit_label': 'Enregistrer',
        'production': production,
    })

@login_required
@user_passes_test(is_manager_or_admin, login_url='accounts:login')
def production_stats(request):
    totals = Production.objects.aggregate(
        total_qty=Sum('quantity'),
        total_val=Sum('estimated_price')
    )
    
    by_product = Production.objects.values(
        'product__name'
    ).annotate(
        qty=Sum('quantity'),
        val=Sum('estimated_price')
    ).order_by('-qty')
    
    return render(request, 'productions/production_stats.html', {
        'total_qty': totals['total_qty'] or 0,
        'total_val': totals['total_val'] or 0,
        'by_product': by_product,
    })
