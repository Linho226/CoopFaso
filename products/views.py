from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ProductForm
from .models import Product

def can_manage_products(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    role = getattr(getattr(user, 'profile', None), 'role', None)
    return role in {'ADMIN', 'COOPERATIVE_MANAGER'}

@login_required
def product_list(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.select_related('cooperative')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(cooperative__name__icontains=query)
        )
    return render(request, 'products/product_list.html', {
        'products': products,
        'query': query,
        'can_manage': can_manage_products(request.user),
    })

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('cooperative'), pk=pk)
    return render(request, 'products/product_detail.html', {
        'product': product,
        'can_manage': can_manage_products(request.user),
    })

@user_passes_test(can_manage_products, login_url='accounts:login')
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Produit publie avec succes.')
            return redirect(product)
    else:
        form = ProductForm()
    return render(request, 'products/product_form.html', {
        'form': form,
        'title': 'Publier un produit',
        'submit_label': 'Publier',
    })

@user_passes_test(can_manage_products, login_url='accounts:login')
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Produit modifie avec succes.')
            return redirect(product)
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/product_form.html', {
        'form': form,
        'title': 'Modifier le produit',
        'submit_label': 'Enregistrer',
        'product': product,
    })

@user_passes_test(can_manage_products, login_url='accounts:login')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Produit supprime avec succes.')
        return redirect('products:list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})
