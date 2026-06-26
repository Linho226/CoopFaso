from django.db import models
from django.urls import reverse


class Cooperative(models.Model):
    name = models.CharField('nom', max_length=180, unique=True)
    address = models.CharField('adresse', max_length=255)
    phone = models.CharField('telephone', max_length=30)
    email = models.EmailField('email')
    region = models.CharField('region', max_length=120)
    province = models.CharField('province', max_length=120)
    creation_date = models.DateField('date de creation')
    description = models.TextField('presentation', blank=True)
    logo = models.ImageField('logo', upload_to='cooperatives/logos/', blank=True, null=True)
    location_url = models.URLField('lien de localisation', blank=True)
    is_public = models.BooleanField('visible publiquement', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'cooperative'
        verbose_name_plural = 'cooperatives'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('cooperatives:detail', kwargs={'pk': self.pk})
