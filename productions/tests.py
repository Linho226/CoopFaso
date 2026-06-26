from decimal import Decimal
from datetime import date
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from accounts.models import UserProfile
from cooperatives.models import Cooperative
from members.models import Member
from products.models import Product
from .models import Production

class ProductionTests(TestCase):
    def setUp(self):
        self.cooperative = Cooperative.objects.create(
            name="Coop Faso Test Production",
            address="Ouagadougou",
            phone="+22670000000",
            email="production@coopfaso.bf",
            region="Centre",
            province="Kadiogo",
            creation_date=date(2026, 1, 1),
        )
        self.manager = User.objects.create_user(username="manager_pr", password="Password123!")
        self.manager.profile.role = UserProfile.Role.COOPERATIVE_MANAGER
        self.manager.profile.cooperative = self.cooperative
        self.manager.profile.save()

        self.farmer_user = User.objects.create_user(username="farmer_pr", password="Password123!", first_name="Jean", last_name="Kabore")
        self.farmer_user.profile.role = UserProfile.Role.FARMER
        self.farmer_user.profile.phone = "+22675000005"
        self.farmer_user.profile.cooperative = self.cooperative
        self.farmer_user.profile.save()

        self.member = Member.objects.create(
            last_name="Kabore",
            first_name="Jean",
            gender=Member.Gender.MALE,
            birth_date=date(1985, 3, 10),
            phone="+22675000005",
            address="Secteur 30",
            cooperative=self.cooperative,
            is_active=True,
        )

        self.product = Product.objects.create(
            cooperative=self.cooperative,
            name="Coton",
            price=300.00,
            quantity_available=1000.00,
        )

        self.production = Production.objects.create(
            member=self.member,
            product=self.product,
            quantity=100.00,
            harvest_date=date(2026, 6, 24),
        )

    def test_estimated_price_calculated_automatically(self):
        self.assertEqual(self.production.estimated_price, 30000.00)

    def test_farmer_can_list_own_productions(self):
        self.client.force_login(self.farmer_user)
        response = self.client.get(reverse('productions:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Coton")
        self.assertContains(response, "Jean Kabore")

    def test_farmer_can_declare_harvest_and_updates_stock(self):
        self.client.force_login(self.farmer_user)
        
        self.product.refresh_from_db()
        initial_stock = self.product.quantity_available
        
        payload = {
            'product': self.product.pk,
            'quantity': '200.00',
            'harvest_date': '2026-06-25',
        }
        response = self.client.post(reverse('productions:create'), payload)
        self.assertEqual(response.status_code, 302)
        
        new_prod = Production.objects.get(harvest_date='2026-06-25')
        self.assertEqual(new_prod.quantity, 200.00)
        self.assertEqual(new_prod.member, self.member)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_available, initial_stock + Decimal('200.00'))

    def test_manager_can_view_stats(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse('productions:stats'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Analyse des Productions")
        self.assertContains(response, "Coton")

    def test_production_rejects_member_and_product_from_different_cooperatives(self):
        other_cooperative = Cooperative.objects.create(
            name='Autre Coop Production',
            address='Bobo',
            phone='+22670000009',
            email='autre-production@coopfaso.bf',
            region='Hauts-Bassins',
            province='Houet',
            creation_date=date(2026, 1, 2),
        )
        other_product = Product.objects.create(
            cooperative=other_cooperative,
            name='Riz autre',
            price=200,
            quantity_available=10,
        )

        with self.assertRaises(ValidationError):
            Production.objects.create(
                member=self.member,
                product=other_product,
                quantity=5,
                harvest_date=date(2026, 6, 25),
            )
