from django.conf import settings
from django.db import models


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
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.FARMER)
    phone = models.CharField('telephone', max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'profil utilisateur'
        verbose_name_plural = 'profils utilisateurs'

    def __str__(self):
        return f'{self.user.get_username()} - {self.get_role_display()}'
