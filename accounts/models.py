from django.conf import settings
from django.db import models

from cooperatives.models import Cooperative


class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrateur'
        COOPERATIVE_MANAGER = 'COOPERATIVE_MANAGER', 'Responsable de cooperative'
        FARMER = 'FARMER', 'Agriculteur'
        BUYER = 'BUYER', 'Acheteur'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.BUYER)
    phone = models.CharField('telephone', max_length=30, blank=True)
    cooperative = models.ForeignKey(
        Cooperative,
        on_delete=models.SET_NULL,
        related_name='user_profiles',
        verbose_name='cooperative rattachee',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'profil utilisateur'
        verbose_name_plural = 'profils utilisateurs'

    def __str__(self):
        return f'{self.user.get_username()} - {self.get_role_display()}'
