from datetime import date
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from accounts.models import UserProfile
from cooperatives.models import Cooperative
from .models import Product

class ProductTests(TestCase):
    def setUp(self):
        self.cooperative = Cooperative.objects.create(
            name="Coop Faso Test Products",
            address="Ouagadougou",
            phone="+22670000000",
            email="products@coopfaso.bf",
            region="Centre",
            province="Kadiogo",
            creation_date=date(2026, 1, 1),
        )
        self.manager = User.objects.create_user(username="manager_p", password="Password123!")
        self.manager.profile.role = UserProfile.Role.COOPERATIVE_MANAGER
        self.manager.profile.save()

        self.farmer = User.objects.create_user(username="farmer_p", password="Password123!")
        self.farmer.profile.role = UserProfile.Role.FARMER
        self.farmer.profile.save()

        self.product = Product.objects.create(
            cooperative=self.cooperative,
            name="Mais",
            description="Mais local",
            price=250.00,
            quantity_available=100.00,
        )

    def test_authenticated_user_can_view_products(self):
        self.client.force_login(self.farmer)
        response = self.client.get(reverse('products:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mais")

        response_detail = self.client.get(reverse('products:detail', args=[self.product.pk]))
        self.assertEqual(response_detail.status_code, 200)
        self.assertContains(response_detail, "Mais local")

    def test_manager_can_create_and_delete_product(self):
        self.client.force_login(self.manager)
        
        # Create
        payload = {
            'cooperative': self.cooperative.pk,
            'name': 'Riz',
            'description': 'Riz local',
            'price': 400.00,
            'quantity_available': 50.00,
        }
        response = self.client.post(reverse('products:create'), payload)
        self.assertEqual(response.status_code, 302)
        new_prod = Product.objects.get(name='Riz')
        self.assertEqual(new_prod.price, 400.00)

        # Delete
        response_del = self.client.post(reverse('products:delete', args=[new_prod.pk]))
        self.assertEqual(response_del.status_code, 302)
        self.assertFalse(Product.objects.filter(name='Riz').exists())

    def test_farmer_cannot_create_or_delete_product(self):
        self.client.force_login(self.farmer)
        payload = {
            'cooperative': self.cooperative.pk,
            'name': 'Sorgho',
            'description': 'Sorgho local',
            'price': 300.00,
            'quantity_available': 20.00,
        }
        response = self.client.post(reverse('products:create'), payload)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(name='Sorgho').exists())
