from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from cooperatives.models import Cooperative
from products.models import Product
from accounts.models import UserProfile

from .models import Order


class SalesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='buyer',
            password='Password123!',
        )
        self.other_user = User.objects.create_user(
            username='other',
            password='Password123!',
        )
        self.user.profile.role = UserProfile.Role.BUYER
        self.user.profile.save()
        self.other_user.profile.role = UserProfile.Role.BUYER
        self.other_user.profile.save()
        cooperative = Cooperative.objects.create(
            name='Coop Vente Test',
            address='Ouagadougou',
            phone='+22670000000',
            email='vente@test.bf',
            region='Centre',
            province='Kadiogo',
            creation_date=date(2025, 1, 1),
        )
        self.product = Product.objects.create(
            cooperative=cooperative,
            name='Riz local',
            price=Decimal('500.00'),
            quantity_available=Decimal('10.00'),
        )
        self.client.force_login(self.user)

    def test_cart_and_checkout_create_order_and_reduce_stock(self):
        response = self.client.post(
            reverse('sales:cart_add', args=[self.product.pk]),
            {'quantity': 3},
        )
        self.assertRedirects(response, reverse('sales:cart'))

        response = self.client.post(reverse('sales:checkout'), {
            'delivery_address': 'Secteur 15, Ouagadougou',
            'phone': '+22670112233',
            'notes': 'Appeler avant livraison',
        })

        order = Order.objects.get(customer=self.user)
        self.assertRedirects(
            response,
            reverse('payments:pay', args=[order.pk]),
        )
        self.assertEqual(order.total_amount, Decimal('1500.00'))
        self.assertEqual(order.items.get().product_name, 'Riz local')
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_available, Decimal('7.00'))

    def test_cannot_add_more_than_available_stock(self):
        self.client.post(
            reverse('sales:cart_add', args=[self.product.pk]),
            {'quantity': 11},
        )
        response = self.client.get(reverse('sales:cart'))
        self.assertNotContains(response, 'Riz local')

    def test_user_cannot_view_another_users_order(self):
        order = Order.objects.create(
            customer=self.other_user,
            delivery_address='Bobo-Dioulasso',
            phone='+22670000001',
            total_amount=Decimal('500.00'),
        )
        response = self.client.get(
            reverse('sales:order_detail', args=[order.pk])
        )
        self.assertEqual(response.status_code, 404)
