import uuid

from django.db import models
from django.urls import reverse

from sales.models import Order


class Payment(models.Model):
    class Method(models.TextChoices):
        ORANGE_MONEY = 'ORANGE_MONEY', 'Orange Money'
        WAVE = 'WAVE', 'Wave'
        CARD = 'CARD', 'Carte bancaire (simulation)'

    class Status(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Reussi'
        FAILED = 'FAILED', 'Echoue'

    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name='payment',
        verbose_name='commande',
    )
    reference = models.CharField(max_length=24, unique=True, editable=False)
    method = models.CharField(max_length=24, choices=Method.choices)
    status = models.CharField(max_length=12, choices=Status.choices)
    amount = models.DecimalField('montant (FCFA)', max_digits=14, decimal_places=2)
    payer_phone = models.CharField('telephone payeur', max_length=30, blank=True)
    card_last4 = models.CharField('4 derniers chiffres', max_length=4, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'paiement'
        verbose_name_plural = 'paiements'

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f'PAY-{uuid.uuid4().hex[:10].upper()}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference

    def get_absolute_url(self):
        return reverse('payments:receipt', kwargs={'pk': self.pk})
