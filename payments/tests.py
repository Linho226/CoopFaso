from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from sales.models import Order
from accounts.models import UserProfile

from .models import Payment


class PaymentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='payer',
            password='Password123!',
        )
        self.user.profile.role = UserProfile.Role.BUYER
        self.user.profile.save()
        self.order = Order.objects.create(
            customer=self.user,
            delivery_address='Ouagadougou',
            phone='+22670000000',
            total_amount=Decimal('2500.00'),
        )
        self.client.force_login(self.user)

    def test_mobile_money_payment_marks_order_paid_and_creates_receipt(self):
        response = self.client.post(
            reverse('payments:pay', args=[self.order.pk]),
            {
                'method': Payment.Method.ORANGE_MONEY,
                'phone': '+22670000000',
                'card_number': '',
            },
        )

        payment = Payment.objects.get(order=self.order)
        self.assertRedirects(
            response,
            reverse('payments:receipt', args=[payment.pk]),
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertEqual(payment.amount, self.order.total_amount)

    def test_order_cannot_be_paid_twice(self):
        payment = Payment.objects.create(
            order=self.order,
            method=Payment.Method.WAVE,
            status=Payment.Status.SUCCESS,
            amount=self.order.total_amount,
        )
        response = self.client.get(
            reverse('payments:pay', args=[self.order.pk])
        )
        self.assertRedirects(
            response,
            reverse('payments:receipt', args=[payment.pk]),
        )

    def test_card_payment_stores_only_last_four_digits(self):
        self.client.post(
            reverse('payments:pay', args=[self.order.pk]),
            {
                'method': Payment.Method.CARD,
                'phone': '',
                'card_number': '4242 4242 4242 1234',
            },
        )
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.card_last4, '1234')
