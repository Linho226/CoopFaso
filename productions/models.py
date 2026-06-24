from django.db import models
from django.urls import reverse
from members.models import Member
from products.models import Product

class Production(models.Model):
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='productions',
        verbose_name='membre',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='productions',
        verbose_name='produit',
    )
    quantity = models.DecimalField('quantite recoltee', max_digits=10, decimal_places=2)
    harvest_date = models.DateField('date de recolte')
    estimated_price = models.DecimalField('prix estimatif (FCFA)', max_digits=12, decimal_places=2, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-harvest_date',)
        verbose_name = 'production'
        verbose_name_plural = 'productions'

    def __str__(self):
        return f"{self.member.full_name} - {self.product.name} - {self.quantity}"

    def save(self, *args, **kwargs):
        if not self.estimated_price:
            self.estimated_price = self.quantity * self.product.price
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('productions:list')
