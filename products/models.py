from django.db import models
from django.urls import reverse
from cooperatives.models import Cooperative


class ProductCategory(models.Model):
    name = models.CharField('nom', max_length=100, unique=True)
    description = models.TextField('description', blank=True)
    is_active = models.BooleanField('active', default=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'categorie de produit'
        verbose_name_plural = 'categories de produits'

    def __str__(self):
        return self.name


class Product(models.Model):
    cooperative = models.ForeignKey(
        Cooperative,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='cooperative',
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        related_name='products',
        verbose_name='categorie',
        blank=True,
        null=True,
    )
    name = models.CharField('nom du produit', max_length=120)
    description = models.TextField('description', blank=True)
    price = models.DecimalField('prix (FCFA)', max_digits=10, decimal_places=2)
    quantity_available = models.DecimalField('quantite disponible', max_digits=10, decimal_places=2, default=0.0)
    image = models.ImageField('image', upload_to='products/images/', blank=True, null=True)
    is_published = models.BooleanField('visible dans le catalogue public', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'produit'
        verbose_name_plural = 'produits'

    def __str__(self):
        return f"{self.name} ({self.cooperative.name})"

    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'pk': self.pk})
