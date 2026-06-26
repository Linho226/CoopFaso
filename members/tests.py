from datetime import date
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from accounts.models import UserProfile
from cooperatives.models import Cooperative
from .models import Member

class MemberTests(TestCase):
    def setUp(self):
        self.cooperative = Cooperative.objects.create(
            name="Coop Faso Test",
            address="Ouagadougou",
            phone="+22670000000",
            email="test@coopfaso.bf",
            region="Centre",
            province="Kadiogo",
            creation_date=date(2026, 1, 1),
        )
        self.manager = User.objects.create_user(username="manager", password="Password123!")
        self.manager.profile.role = UserProfile.Role.COOPERATIVE_MANAGER
        self.manager.profile.cooperative = self.cooperative
        self.manager.profile.save()

        self.farmer = User.objects.create_user(username="farmer", password="Password123!")
        self.farmer.profile.role = UserProfile.Role.FARMER
        self.farmer.profile.save()

        self.member = Member.objects.create(
            last_name="Sawadogo",
            first_name="Issa",
            gender=Member.Gender.MALE,
            birth_date=date(1990, 5, 15),
            phone="+22676000000",
            address="Secteur 15, Ouaga",
            cooperative=self.cooperative,
            is_active=True,
        )
        self.other_cooperative = Cooperative.objects.create(
            name='Autre cooperative',
            address='Bobo',
            phone='+22670000009',
            email='autre@coopfaso.bf',
            region='Hauts-Bassins',
            province='Houet',
            creation_date=date(2026, 1, 2),
        )
        self.other_member = Member.objects.create(
            last_name='Autre',
            first_name='Membre',
            gender=Member.Gender.FEMALE,
            birth_date=date(1992, 1, 1),
            phone='+22676000009',
            address='Bobo',
            cooperative=self.other_cooperative,
        )

    def test_farmer_cannot_list_members(self):
        self.client.force_login(self.farmer)
        response = self.client.get(reverse('members:list'))
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_manager_can_search_own_members(self):
        self.client.force_login(self.manager)
        # Search by name
        response = self.client.get(reverse('members:list') + '?q=Sawadogo')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sawadogo")

        # Search by non-existent name
        response = self.client.get(reverse('members:list') + '?q=Nonexistent')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Sawadogo")

    def test_manager_never_sees_members_from_another_cooperative(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse('members:list'))

        self.assertContains(response, 'Sawadogo')
        self.assertNotContains(response, 'Autre cooperative')
        self.assertNotContains(response, '+22676000009')

    def test_admin_can_filter_members_by_cooperative(self):
        admin = User.objects.create_user(
            username='members_admin',
            password='Password123!',
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.get(
            reverse('members:list'),
            {'cooperative': self.other_cooperative.pk},
        )

        self.assertContains(response, 'Autre cooperative')
        self.assertContains(response, 'Membre')
        self.assertNotContains(response, 'Sawadogo')

    def test_farmer_cannot_view_member_detail(self):
        self.client.force_login(self.farmer)
        response = self.client.get(reverse('members:detail', args=[self.member.pk]))
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_manager_can_create_member(self):
        self.client.force_login(self.manager)
        payload = {
            'last_name': 'Ouédraogo',
            'first_name': 'Fatoumata',
            'gender': Member.Gender.FEMALE,
            'birth_date': '1995-08-20',
            'phone': '+22675000000',
            'address': 'Koudougou',
            'cooperative': self.cooperative.pk,
        }
        response = self.client.post(reverse('members:create'), payload)
        self.assertEqual(response.status_code, 302)
        
        new_member = Member.objects.get(last_name='Ouédraogo')
        self.assertEqual(new_member.first_name, 'Fatoumata')
        self.assertEqual(new_member.gender, Member.Gender.FEMALE)
        self.assertEqual(new_member.cooperative, self.cooperative)

    def test_farmer_cannot_create_member(self):
        self.client.force_login(self.farmer)
        payload = {
            'last_name': 'Ouédraogo',
            'first_name': 'Fatoumata',
            'gender': Member.Gender.FEMALE,
            'birth_date': '1995-08-20',
            'phone': '+22675000000',
            'address': 'Koudougou',
            'cooperative': self.cooperative.pk,
        }
        response = self.client.post(reverse('members:create'), payload)
        # Should redirect to login (or be denied) because of user_passes_test
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Member.objects.filter(last_name='Ouédraogo').exists())

    def test_manager_can_update_member(self):
        self.client.force_login(self.manager)
        payload = {
            'last_name': 'Sawadogo',
            'first_name': 'Issa Modifié',
            'gender': Member.Gender.MALE,
            'birth_date': '1990-05-15',
            'phone': '+22676000001',
            'address': 'Secteur 15, Ouaga',
            'cooperative': self.cooperative.pk,
        }
        response = self.client.post(reverse('members:update', args=[self.member.pk]), payload)
        self.assertEqual(response.status_code, 302)
        
        self.member.refresh_from_db()
        self.assertEqual(self.member.first_name, 'Issa Modifié')
        self.assertEqual(self.member.phone, '+22676000001')

    def test_manager_can_deactivate_member(self):
        self.client.force_login(self.manager)
        # GET confirm page
        response = self.client.get(reverse('members:deactivate', args=[self.member.pk]))
        self.assertEqual(response.status_code, 200)
        
        # POST deactivate
        response = self.client.post(reverse('members:deactivate', args=[self.member.pk]))
        self.assertEqual(response.status_code, 302)
        
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)
