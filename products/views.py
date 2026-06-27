from django.contrib import messages
from django.db.models import Prefetch, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.access import is_manager, roles_required, user_cooperative
from accounts.models import UserProfile
from cooperatives.models import Cooperative

from .forms import ProductForm
from .models import Product


def _selected_cooperative(request):
    if is_manager(request.user):
        return user_cooperative(request.user)
    cooperative_id = request.GET.get('cooperative') or request.POST.get('cooperative')
    if cooperative_id:
        return Cooperative.objects.filter(pk=cooperative_id).first()
    return None


@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.COOPERATIVE_MANAGER)
def product_list(request):
    query = request.GET.get('q', '').strip()
    selected_cooperative = request.GET.get('cooperative', '').strip()
    products = Product.objects.select_related('cooperative')
    if is_manager(request.user):
        manager_cooperative = user_cooperative(request.user)
        products = products.filter(cooperative=manager_cooperative)
        selected_cooperative = str(getattr(manager_cooperative, 'pk', ''))
    elif selected_cooperative:
        products = products.filter(cooperative_id=selected_cooperative)
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(cooperative__name__icontains=query)
        )
    cooperative_groups = Cooperative.objects.all()
    if selected_cooperative:
        cooperative_groups = cooperative_groups.filter(pk=selected_cooperative)
    cooperative_groups = cooperative_groups.prefetch_related(
        Prefetch('products', queryset=products, to_attr='filtered_products')
    ).annotate(stock_total=Sum('products__quantity_available'))
    return render(request, 'products/product_list.html', {
        'products': products,
        'cooperative_groups': cooperative_groups,
        'cooperatives': Cooperative.objects.all(),
        'query': query,
        'selected_cooperative': selected_cooperative,
        'is_manager_view': is_manager(request.user),
        'can_manage': True,
    })

@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.COOPERATIVE_MANAGER)
def product_detail(request, pk):
    products = Product.objects.select_related('cooperative')
    if is_manager(request.user):
        products = products.filter(cooperative=user_cooperative(request.user))
    product = get_object_or_404(products, pk=pk)
    return render(request, 'products/product_detail.html', {
        'product': product,
        'can_manage': True,
    })

@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.COOPERATIVE_MANAGER)
def product_create(request):
    cooperative = _selected_cooperative(request)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, cooperative=cooperative)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Produit publie avec succes.')
            return redirect(product)
    else:
        form = ProductForm(cooperative=cooperative)
    return render(request, 'products/product_form.html', {
        'form': form,
        'title': 'Publier un produit',
        'submit_label': 'Publier',
    })

@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.COOPERATIVE_MANAGER)
def product_update(request, pk):
    products = Product.objects.all()
    if is_manager(request.user):
        products = products.filter(cooperative=user_cooperative(request.user))
    product = get_object_or_404(products, pk=pk)
    cooperative = user_cooperative(request.user) if is_manager(request.user) else None
    if request.method == 'POST':
        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product,
            cooperative=cooperative,
        )
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Produit modifie avec succes.')
            return redirect(product)
    else:
        form = ProductForm(instance=product, cooperative=cooperative)
    return render(request, 'products/product_form.html', {
        'form': form,
        'title': 'Modifier le produit',
        'submit_label': 'Enregistrer',
        'product': product,
    })

@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.COOPERATIVE_MANAGER)
def product_delete(request, pk):
    products = Product.objects.all()
    if is_manager(request.user):
        products = products.filter(cooperative=user_cooperative(request.user))
    product = get_object_or_404(products, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Produit supprime avec succes.')
        return redirect('products:list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})
