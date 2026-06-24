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

    def test_authenticated_user_can_list_members(self):
        self.client.force_login(self.farmer)
        response = self.client.get(reverse('members:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sawadogo")
        self.assertContains(response, "Issa")

    def test_member_search(self):
        self.client.force_login(self.farmer)
        # Search by name
        response = self.client.get(reverse('members:list') + '?q=Sawadogo')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sawadogo")

        # Search by non-existent name
        response = self.client.get(reverse('members:list') + '?q=Nonexistent')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Sawadogo")

    def test_authenticated_user_can_view_member_detail(self):
        self.client.force_login(self.farmer)
        response = self.client.get(reverse('members:detail', args=[self.member.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sawadogo")
        self.assertContains(response, "Issa")

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
