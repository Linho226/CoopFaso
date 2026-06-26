from decimal import Decimal

from products.models import Product


CART_SESSION_KEY = 'cart'


def get_cart(request):
    return request.session.get(CART_SESSION_KEY, {})


def save_cart(request, cart):
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


def cart_details(request):
    cart = get_cart(request)
    products = Product.objects.filter(pk__in=cart.keys()).select_related('cooperative')
    items = []
    total = Decimal('0')
    count = 0

    for product in products:
        quantity = int(cart.get(str(product.pk), 0))
        if quantity < 1:
            continue
        subtotal = product.price * quantity
        items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })
        total += subtotal
        count += quantity

    return {'items': items, 'total': total, 'count': count}


def cart_count(request):
    if (
        not request.user.is_authenticated
        or getattr(getattr(request.user, 'profile', None), 'role', None) != 'BUYER'
    ):
        return {'cart_count': 0}
    return {'cart_count': cart_details(request)['count']}
