from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.access import is_admin, is_manager, roles_required, user_cooperative
from accounts.models import UserProfile
from sales.models import Order

from .forms import PaymentForm
from .models import Payment


@roles_required(UserProfile.Role.BUYER)
def pay_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id, customer=request.user)
    if hasattr(order, 'payment'):
        return redirect('payments:receipt', pk=order.payment.pk)

    if request.method == 'POST':
        form = PaymentForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                order = Order.objects.select_for_update().get(pk=order.pk)
                if hasattr(order, 'payment'):
                    return redirect('payments:receipt', pk=order.payment.pk)
                method = form.cleaned_data['method']
                card_number = form.cleaned_data['card_number']
                payment = Payment.objects.create(
                    order=order,
                    method=method,
                    status=Payment.Status.SUCCESS,
                    amount=order.total_amount,
                    payer_phone=form.cleaned_data['phone'] if method != Payment.Method.CARD else '',
                    card_last4=card_number[-4:] if method == Payment.Method.CARD else '',
                    paid_at=timezone.now(),
                )
                order.status = Order.Status.PAID
                order.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Paiement simule avec succes. Votre recu est disponible.')
            return redirect('payments:receipt', pk=payment.pk)
    else:
        form = PaymentForm(user=request.user)

    return render(request, 'payments/pay.html', {
        'order': order,
        'form': form,
        'base_template': 'public_site/base.html',
    })


@roles_required(
    UserProfile.Role.ADMIN,
    UserProfile.Role.COOPERATIVE_MANAGER,
    UserProfile.Role.BUYER,
)
def payment_history(request):
    payments = Payment.objects.select_related('order')
    if is_manager(request.user):
        cooperative = user_cooperative(request.user)
        payments = payments.filter(
            order__items__product__cooperative=cooperative
        ).distinct().annotate(
            visible_amount=Sum(
                'order__items__subtotal',
                filter=Q(order__items__product__cooperative=cooperative),
            )
        )
    elif not is_admin(request.user):
        payments = payments.filter(order__customer=request.user)
    return render(request, 'payments/history.html', {
        'payments': payments,
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
def receipt(request, pk):
    payments = Payment.objects.select_related(
        'order', 'order__customer'
    ).prefetch_related('order__items')
    if is_manager(request.user):
        payments = payments.filter(
            order__items__product__cooperative=user_cooperative(request.user)
        ).distinct()
    elif not is_admin(request.user):
        payments = payments.filter(order__customer=request.user)
    payment = get_object_or_404(payments, pk=pk)
    items = payment.order.items.select_related('product')
    visible_amount = payment.amount
    if is_manager(request.user):
        items = items.filter(product__cooperative=user_cooperative(request.user))
        visible_amount = items.aggregate(total=Sum('subtotal'))['total'] or 0
    return render(request, 'payments/receipt.html', {
        'payment': payment,
        'items': items,
        'visible_amount': visible_amount,
        'base_template': (
            'public_site/base.html'
            if not is_admin(request.user) and not is_manager(request.user)
            else 'accounts/base.html'
        ),
    })
