from django.db import models
from django.urls import reverse

from cooperatives.models import Cooperative


class Member(models.Model):
    class Gender(models.TextChoices):
        MALE = 'M', 'Masculin'
        FEMALE = 'F', 'Feminin'

    last_name = models.CharField('nom', max_length=120)
    first_name = models.CharField('prenom', max_length=120)
    gender = models.CharField('sexe', max_length=1, choices=Gender.choices)
    birth_date = models.DateField('date de naissance')
    phone = models.CharField('telephone', max_length=30)
    address = models.CharField('adresse', max_length=255)
    photo = models.ImageField('photo', upload_to='members/photos/', blank=True, null=True)
    cooperative = models.ForeignKey(
        Cooperative,
        on_delete=models.PROTECT,
        related_name='members',
        verbose_name='cooperative',
    )
    is_active = models.BooleanField('actif', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('last_name', 'first_name')
        verbose_name = 'membre'
        verbose_name_plural = 'membres'

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_absolute_url(self):
        return reverse('members:detail', kwargs={'pk': self.pk})
