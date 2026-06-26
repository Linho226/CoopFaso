from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from datetime import date
from decimal import Decimal
from django.utils import timezone

from cooperatives.models import Cooperative
from members.models import Member
from payments.models import Payment
from productions.models import Production
from products.models import Product
from public_site.models import ContactMessage
from sales.models import Order, OrderItem
from .models import UserProfile


class AuthenticationTests(TestCase):
    def test_public_registration_always_creates_buyer_profile(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'amina',
                'first_name': 'Amina',
                'last_name': 'Sawadogo',
                'email': 'amina@example.com',
                'phone': '+22600000000',
                'password1': 'MotdepasseFort123!',
                'password2': 'MotdepasseFort123!',
            },
        )

        self.assertRedirects(response, reverse('accounts:login'))
        user = User.objects.get(username='amina')
        self.assertEqual(user.profile.role, UserProfile.Role.BUYER)
        self.assertEqual(user.profile.phone, '+22600000000')

    def test_public_registration_ignores_submitted_privileged_role(self):
        self.client.post(
            reverse('accounts:register'),
            {
                'username': 'manager_attempt',
                'first_name': 'Tentative',
                'last_name': 'Manager',
                'email': 'manager-attempt@example.com',
                'phone': '+22670000000',
                'role': UserProfile.Role.COOPERATIVE_MANAGER,
                'password1': 'MotdepasseFort123!',
                'password2': 'MotdepasseFort123!',
            },
        )

        user = User.objects.get(username='manager_attempt')
        self.assertEqual(user.profile.role, UserProfile.Role.BUYER)

    def test_role_management_requires_admin_user(self):
        user = User.objects.create_user(username='agri', password='MotdepasseFort123!')
        self.client.force_login(user)

        response = self.client.get(reverse('accounts:user_roles'))

        self.assertEqual(response.status_code, 302)

    def test_staff_user_can_update_role(self):
        staff = User.objects.create_user(username='admin', password='MotdepasseFort123!', is_staff=True)
        managed = User.objects.create_user(username='acheteur', password='MotdepasseFort123!')
        self.client.force_login(staff)

        response = self.client.post(
            reverse('accounts:update_user_role', args=[managed.id]),
            {'role': UserProfile.Role.BUYER},
        )

        self.assertRedirects(response, reverse('accounts:user_roles'))
        managed.profile.refresh_from_db()
        self.assertEqual(managed.profile.role, UserProfile.Role.BUYER)


class AdminSiteTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='Password123!',
        )

    def test_admin_index_redirects_to_platform_dashboard(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin:index'))

        self.assertRedirects(response, reverse('accounts:dashboard'))


class AnalyticsDashboardTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='analytics_admin',
            email='analytics@example.com',
            password='Password123!',
        )
        self.cooperative = Cooperative.objects.create(
            name='Cooperative Analytics',
            address='Ouagadougou',
            phone='+22670000000',
            email='analytics@coop.bf',
            region='Centre',
            province='Kadiogo',
            creation_date=date(2025, 1, 1),
        )
        self.member = Member.objects.create(
            last_name='Kabore',
            first_name='Awa',
            gender=Member.Gender.FEMALE,
            birth_date=date(1990, 1, 1),
            phone='+22670000001',
            address='Ouagadougou',
            cooperative=self.cooperative,
        )
        self.product = Product.objects.create(
            cooperative=self.cooperative,
            name='Mais Analytics',
            price=Decimal('500'),
            quantity_available=Decimal('5'),
        )
        Production.objects.create(
            member=self.member,
            product=self.product,
            quantity=Decimal('20'),
            harvest_date=timezone.localdate(),
        )
        order = Order.objects.create(
            customer=self.admin,
            delivery_address='Ouagadougou',
            phone='+22670000000',
            total_amount=Decimal('1500'),
            status=Order.Status.PAID,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            unit_price=Decimal('500'),
            quantity=3,
            subtotal=Decimal('1500'),
        )
        Payment.objects.create(
            order=order,
            method=Payment.Method.WAVE,
            status=Payment.Status.SUCCESS,
            amount=Decimal('1500'),
            paid_at=timezone.now(),
        )

    def test_admin_dashboard_contains_charts_and_business_metrics(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('accounts:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Revenus des 6 derniers mois')
        self.assertContains(response, 'Repartition des statuts')
        self.assertEqual(response.context['global_revenue'], Decimal('1500'))
        self.assertEqual(response.context['products_sold'], 3)
        self.assertEqual(len(response.context['monthly_revenue']), 6)
        self.assertEqual(
            response.context['production_by_product'][0]['label'],
            'Mais Analytics',
        )


class RoleAccessTests(TestCase):
    def setUp(self):
        self.cooperative = Cooperative.objects.create(
            name='Cooperative roles',
            address='Ouagadougou',
            phone='+22670000000',
            email='roles@coop.bf',
            region='Centre',
            province='Kadiogo',
            creation_date=date(2026, 1, 1),
        )

    def create_user(self, username, role):
        user = User.objects.create_user(username=username, password='Password123!')
        user.profile.role = role
        user.profile.cooperative = self.cooperative
        user.profile.save()
        return user

    def test_farmer_dashboard_hides_buyer_and_management_modules(self):
        farmer = self.create_user('farmer_access', UserProfile.Role.FARMER)
        self.client.force_login(farmer)

        response = self.client.get(reverse('accounts:dashboard'))

        self.assertContains(response, 'Mes productions')
        self.assertContains(response, 'Formations')
        self.assertNotContains(response, reverse('sales:cart'))
        self.assertNotContains(response, reverse('members:list'))
        self.assertNotContains(response, reverse('cooperatives:list'))

    def test_farmer_cannot_open_buyer_cart(self):
        farmer = self.create_user('farmer_cart', UserProfile.Role.FARMER)
        self.client.force_login(farmer)

        response = self.client.get(reverse('sales:cart'))

        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_buyer_sees_purchase_modules_but_not_agricultural_management(self):
        buyer = self.create_user('buyer_access', UserProfile.Role.BUYER)
        self.client.force_login(buyer)

        response = self.client.get(reverse('accounts:dashboard'))

        self.assertRedirects(response, reverse('public_site:home'))

    def test_buyer_pages_use_public_layout(self):
        buyer = self.create_user('buyer_public_layout', UserProfile.Role.BUYER)
        self.client.force_login(buyer)

        for url in (
            reverse('sales:cart'),
            reverse('sales:order_list'),
            reverse('payments:history'),
            reverse('accounts:my_messages'),
            reverse('accounts:profile'),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'public_site/base.html')
                self.assertNotContains(response, 'app-sidebar')

    def test_farmer_login_ignores_buyer_only_next_url(self):
        farmer = self.create_user('farmer_login', UserProfile.Role.FARMER)

        response = self.client.post(
            reverse('accounts:login') + f'?next={reverse("sales:cart")}',
            {'username': farmer.username, 'password': 'Password123!'},
        )

        self.assertRedirects(response, reverse('accounts:dashboard'))


class MessagingTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='message_admin',
            password='Password123!',
            is_staff=True,
        )
        self.buyer = User.objects.create_user(
            username='message_buyer',
            password='Password123!',
            email='buyer@example.com',
        )
        self.message = ContactMessage.objects.create(
            sender=self.buyer,
            category=ContactMessage.Category.ROLE_REQUEST,
            name='Message Buyer',
            email=self.buyer.email,
            subject='Changement de role',
            message='Je souhaite devenir agriculteur.',
        )

    def test_user_sees_only_own_messages(self):
        other = User.objects.create_user(username='other_message')
        ContactMessage.objects.create(
            sender=other,
            name='Other',
            email='other@example.com',
            subject='Message prive',
            message='Contenu prive',
        )
        self.client.force_login(self.buyer)

        response = self.client.get(reverse('accounts:my_messages'))

        self.assertContains(response, 'Changement de role')
        self.assertNotContains(response, 'Message prive')

    def test_admin_can_reply_to_message(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('accounts:message_manage', args=[self.message.pk]),
            {
                'status': ContactMessage.Status.IN_PROGRESS,
                'admin_reply': 'Votre demande est acceptee.',
            },
        )

        self.assertRedirects(
            response,
            reverse('accounts:message_manage', args=[self.message.pk]),
        )
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, ContactMessage.Status.ANSWERED)
        self.assertEqual(self.message.processed_by, self.admin)
        self.assertIsNotNone(self.message.replied_at)

    def test_non_admin_cannot_open_message_inbox(self):
        self.client.force_login(self.buyer)

        response = self.client.get(reverse('accounts:message_inbox'))

        self.assertEqual(response.status_code, 302)

# Create your tests here.
