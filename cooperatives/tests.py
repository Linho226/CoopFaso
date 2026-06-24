from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile

from .models import Cooperative


class CooperativeTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='MotdepasseFort123!', is_staff=True)
        self.farmer = User.objects.create_user(username='agri', password='MotdepasseFort123!')
        self.manager = User.objects.create_user(username='manager', password='MotdepasseFort123!')
        self.manager.profile.role = UserProfile.Role.COOPERATIVE_MANAGER
        self.manager.profile.save()
        self.payload = {
            'name': 'Coop Faso Nord',
            'address': 'Secteur 10, Ouahigouya',
            'phone': '+22670000000',
            'email': 'nord@coopfaso.local',
            'region': 'Nord',
            'province': 'Yatenga',
            'creation_date': '2026-06-24',
        }

    def test_manager_can_create_cooperative(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse('cooperatives:create'), self.payload)

        cooperative = Cooperative.objects.get(name='Coop Faso Nord')
        self.assertRedirects(response, cooperative.get_absolute_url())
        self.assertEqual(cooperative.province, 'Yatenga')

    def test_farmer_can_consult_but_cannot_create(self):
        cooperative = Cooperative.objects.create(
            name='Coop Est',
            address='Fada',
            phone='+22671000000',
            email='est@coopfaso.local',
            region='Est',
            province='Gourma',
            creation_date=date(2026, 6, 24),
        )
        self.client.force_login(self.farmer)

        detail_response = self.client.get(reverse('cooperatives:detail', args=[cooperative.pk]))
        create_response = self.client.get(reverse('cooperatives:create'))

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(create_response.status_code, 302)

    def test_staff_can_update_and_delete_cooperative(self):
        cooperative = Cooperative.objects.create(
            name='Coop Centre',
            address='Ouaga',
            phone='+22672000000',
            email='centre@coopfaso.local',
            region='Centre',
            province='Kadiogo',
            creation_date=date(2026, 6, 24),
        )
        self.client.force_login(self.admin)

        update_payload = self.payload | {'name': 'Coop Centre Plus'}
        update_response = self.client.post(reverse('cooperatives:update', args=[cooperative.pk]), update_payload)
        cooperative.refresh_from_db()
        delete_response = self.client.post(reverse('cooperatives:delete', args=[cooperative.pk]))

        self.assertEqual(update_response.status_code, 302)
        self.assertEqual(update_response['Location'], cooperative.get_absolute_url())
        self.assertEqual(cooperative.name, 'Coop Centre Plus')
        self.assertRedirects(delete_response, reverse('cooperatives:list'))
        self.assertFalse(Cooperative.objects.filter(pk=cooperative.pk).exists())


