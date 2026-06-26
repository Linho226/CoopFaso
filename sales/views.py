from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.access import is_admin, is_manager, roles_required, user_cooperative
from accounts.models import UserProfile
from products.models import Product

from .cart import cart_details, get_cart, save_cart
from .forms import CartAddForm, CheckoutForm
from .models import Order, OrderItem


@roles_required(UserProfile.Role.BUYER)
def cart_detail(request):
    return render(request, 'sales/cart.html', {
        **cart_details(request),
        'base_template': 'public_site/base.html',
    })


@roles_required(UserProfile.Role.BUYER)
def cart_add(request, product_id):
    product = get_object_or_404(
        Product,
        pk=product_id,
        is_published=True,
        quantity_available__gt=0,
    )
    if request.method != 'POST':
        return redirect('public_site:product_detail', pk=product.pk)

    form = CartAddForm(request.POST)
    if form.is_valid():
        quantity = form.cleaned_data['quantity']
        cart = get_cart(request)
        current_quantity = int(cart.get(str(product.pk), 0))
        new_quantity = current_quantity + quantity
        if Decimal(new_quantity) > product.quantity_available:
            messages.error(request, 'La quantite demandee depasse le stock disponible.')
        else:
            cart[str(product.pk)] = new_quantity
            save_cart(request, cart)
            messages.success(request, f'{product.name} ajoute au panier.')
    else:
        messages.error(request, 'Quantite invalide.')
    return redirect(request.POST.get('next') or 'sales:cart')


@roles_required(UserProfile.Role.BUYER)
def cart_update(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_published=True)
    if request.method == 'POST':
        form = CartAddForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            if Decimal(quantity) > product.quantity_available:
                messages.error(request, 'La quantite demandee depasse le stock disponible.')
            else:
                cart = get_cart(request)
                cart[str(product.pk)] = quantity
                save_cart(request, cart)
                messages.success(request, 'Panier mis a jour.')
    return redirect('sales:cart')


@roles_required(UserProfile.Role.BUYER)
def cart_remove(request, product_id):
    if request.method == 'POST':
        cart = get_cart(request)
        cart.pop(str(product_id), None)
        save_cart(request, cart)
        messages.success(request, 'Produit retire du panier.')
    return redirect('sales:cart')


@roles_required(UserProfile.Role.BUYER)
def checkout(request):
    details = cart_details(request)
    if not details['items']:
        messages.info(request, 'Votre panier est vide.')
        return redirect('public_site:products')

    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    locked_products = {
                        product.pk: product
                        for product in Product.objects.select_for_update().filter(
                            pk__in=[item['product'].pk for item in details['items']]
                        )
                    }
                    total = Decimal('0')
                    for item in details['items']:
                        product = locked_products[item['product'].pk]
                        if product.quantity_available < item['quantity']:
                            raise ValueError(
                                f'Stock insuffisant pour {product.name}. '
                                f'Disponible : {product.quantity_available}.'
                            )
                        total += product.price * item['quantity']

                    order = Order.objects.create(
                        customer=request.user,
                        delivery_address=form.cleaned_data['delivery_address'],
                        phone=form.cleaned_data['phone'],
                        notes=form.cleaned_data['notes'],
                        total_amount=total,
                    )
                    for item in details['items']:
                        product = locked_products[item['product'].pk]
                        quantity = item['quantity']
                        subtotal = product.price * quantity
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            product_name=product.name,
                            unit_price=product.price,
                            quantity=quantity,
                            subtotal=subtotal,
                        )
                        product.quantity_available -= quantity
                        product.save(update_fields=['quantity_available', 'updated_at'])
            except ValueError as error:
                messages.error(request, str(error))
            else:
                save_cart(request, {})
                messages.success(request, 'Commande validee. Choisissez votre mode de paiement.')
                return redirect('payments:pay', order_id=order.pk)
    else:
        form = CheckoutForm(user=request.user)

    return render(request, 'sales/checkout.html', {
        'form': form,
        'base_template': 'public_site/base.html',
        **details,
    })


@roles_required(
    UserProfile.Role.ADMIN,
    UserProfile.Role.COOPERATIVE_MANAGER,
    UserProfile.Role.BUYER,
)
def order_list(request):
    if is_admin(request.user):
        orders = Order.objects.prefetch_related('items')
    elif is_manager(request.user):
        cooperative = user_cooperative(request.user)
        orders = Order.objects.filter(
            items__product__cooperative=cooperative
        ).distinct().annotate(
            visible_total=Sum(
                'items__subtotal',
                filter=Q(items__product__cooperative=cooperative),
            )
        ).prefetch_related(
            Prefetch(
                'items',
                queryset=OrderItem.objects.filter(product__cooperative=cooperative),
                to_attr='visible_items',
            )
        )
    else:
        orders = request.user.orders.prefetch_related('items')
    return render(request, 'sales/order_list.html', {
        'orders': orders,
        'is_buyer': not is_admin(request.user) and not is_manager(request.user),
        'is_manager': is_manager(request.user),
        'base_template': (
            'public_site/base.html'
            if not is_admin(request.user) and not is_manager(request.user)
            else 'accounts/base.html'
        ),
    })


@roles_required(
    UserProfile.Role.ADMIN,
    UserProfile.Role.COOPERATIVE_MANAGER,
    UserProfile.Role.BUYER,
)
def order_detail(request, pk):
    orders = Order.objects.all()
    if is_manager(request.user):
        cooperative = user_cooperative(request.user)
        orders = orders.filter(items__product__cooperative=cooperative).distinct()
    elif not is_admin(request.user):
        orders = orders.filter(customer=request.user)
    order = get_object_or_404(orders, pk=pk)
    items = order.items.select_related('product')
    visible_total = order.total_amount
    if is_manager(request.user):
        items = items.filter(product__cooperative=user_cooperative(request.user))
        visible_total = items.aggregate(total=Sum('subtotal'))['total'] or 0
    return render(request, 'sales/order_detail.html', {
        'order': order,
        'items': items,
        'visible_total': visible_total,
        'can_pay': not is_admin(request.user) and not is_manager(request.user),
        'base_template': (
            'public_site/base.html'
            if not is_admin(request.user) and not is_manager(request.user)
            else 'accounts/base.html'
        ),
    })
