from django.db import models
from django.urls import reverse
from cooperatives.models import Cooperative

class Product(models.Model):
    cooperative = models.ForeignKey(
        Cooperative,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='cooperative',
    )
    name = models.CharField('nom du produit', max_length=120)
    description = models.TextField('description', blank=True)
    price = models.DecimalField('prix (FCFA)', max_digits=10, decimal_places=2)
    quantity_available = models.DecimalField('quantite disponible', max_digits=10, decimal_places=2, default=0.0)
    image = models.ImageField('image', upload_to='products/images/', blank=True, null=True)
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
