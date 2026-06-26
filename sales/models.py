import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse

from products.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = 'PENDING_PAYMENT', 'En attente de paiement'
        PAID = 'PAID', 'Payee'
        PROCESSING = 'PROCESSING', 'En preparation'
        DELIVERED = 'DELIVERED', 'Livree'
        CANCELLED = 'CANCELLED', 'Annulee'

    reference = models.CharField(max_length=24, unique=True, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='client',
    )
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
    )
    delivery_address = models.CharField('adresse de livraison', max_length=255)
    phone = models.CharField('telephone', max_length=30)
    notes = models.TextField('instructions', blank=True)
    total_amount = models.DecimalField(
        'montant total (FCFA)',
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'commande'
        verbose_name_plural = 'commandes'

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f'CMD-{uuid.uuid4().hex[:10].upper()}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference

    def get_absolute_url(self):
        return reverse('sales:order_detail', kwargs={'pk': self.pk})


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='commande',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='produit',
    )
    product_name = models.CharField('nom du produit', max_length=120)
    unit_price = models.DecimalField(
        'prix unitaire (FCFA)',
        max_digits=12,
        decimal_places=2,
    )
    quantity = models.PositiveIntegerField('quantite')
    subtotal = models.DecimalField(
        'sous-total (FCFA)',
        max_digits=14,
        decimal_places=2,
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'ligne de commande'
        verbose_name_plural = 'lignes de commande'

    def __str__(self):
        return f'{self.product_name} x {self.quantity}'
