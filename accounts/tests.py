from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import UserProfile


class AuthenticationTests(TestCase):
    def test_registration_creates_user_profile_with_selected_role(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'amina',
                'first_name': 'Amina',
                'last_name': 'Sawadogo',
                'email': 'amina@example.com',
                'phone': '+22600000000',
                'role': UserProfile.Role.FARMER,
                'password1': 'MotdepasseFort123!',
                'password2': 'MotdepasseFort123!',
            },
        )

        self.assertRedirects(response, reverse('accounts:login'))
        user = User.objects.get(username='amina')
        self.assertEqual(user.profile.role, UserProfile.Role.FARMER)
        self.assertEqual(user.profile.phone, '+22600000000')

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

# Create your tests here.
