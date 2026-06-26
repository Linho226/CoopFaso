from django.conf import settings
from django.db import models
from django.urls import reverse


class PlatformInfo(models.Model):
    name = models.CharField('nom de la plateforme', max_length=120, default='CoopFaso')
    headline = models.CharField('titre principal', max_length=220)
    presentation = models.TextField('presentation')
    mission = models.TextField('mission', blank=True)
    phone = models.CharField('telephone', max_length=30, blank=True)
    email = models.EmailField('email', blank=True)
    address = models.CharField('adresse', max_length=255, blank=True)
    hero_image = models.ImageField(
        'image de couverture',
        upload_to='public/hero/',
        blank=True,
        null=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'informations de la plateforme'
        verbose_name_plural = 'informations de la plateforme'

    def __str__(self):
        return self.name


class News(models.Model):
    title = models.CharField('titre', max_length=200)
    summary = models.TextField('resume')
    content = models.TextField('contenu')
    image = models.ImageField('image', upload_to='public/news/', blank=True, null=True)
    is_published = models.BooleanField('publiee', default=True)
    published_at = models.DateTimeField('date de publication')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-published_at',)
        verbose_name = 'actualite agricole'
        verbose_name_plural = 'actualites agricoles'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('public_site:news_detail', kwargs={'pk': self.pk})


class FarmingTip(models.Model):
    title = models.CharField('titre', max_length=180)
    content = models.TextField('conseil')
    theme = models.CharField('theme', max_length=120, blank=True)
    image = models.ImageField('image', upload_to='public/tips/', blank=True, null=True)
    is_published = models.BooleanField('publie', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'conseil agricole'
        verbose_name_plural = 'conseils agricoles'

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    class Category(models.TextChoices):
        ROLE_REQUEST = 'ROLE_REQUEST', 'Demande de role'
        SUPPORT = 'SUPPORT', 'Assistance technique'
        ORDER = 'ORDER', 'Commande ou paiement'
        PARTNERSHIP = 'PARTNERSHIP', 'Partenariat'
        INFORMATION = 'INFORMATION', "Demande d'information"
        OTHER = 'OTHER', 'Autre'

    class Status(models.TextChoices):
        NEW = 'NEW', 'Nouveau'
        IN_PROGRESS = 'IN_PROGRESS', 'En cours'
        ANSWERED = 'ANSWERED', 'Repondu'
        CLOSED = 'CLOSED', 'Cloture'

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='contact_messages',
        verbose_name='utilisateur',
        blank=True,
        null=True,
    )
    category = models.CharField(
        'motif',
        max_length=24,
        choices=Category.choices,
        default=Category.INFORMATION,
    )
    name = models.CharField('nom', max_length=150)
    email = models.EmailField('email')
    phone = models.CharField('telephone', max_length=30, blank=True)
    subject = models.CharField('objet', max_length=180)
    message = models.TextField('message')
    status = models.CharField(
        'statut',
        max_length=16,
        choices=Status.choices,
        default=Status.NEW,
    )
    admin_reply = models.TextField('reponse', blank=True)
    replied_at = models.DateTimeField('date de reponse', blank=True, null=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='processed_contact_messages',
        verbose_name='traite par',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'message de contact'
        verbose_name_plural = 'messages de contact'

    def __str__(self):
        return f'{self.name} - {self.subject}'

    @property
    def is_processed(self):
        return self.status in {self.Status.ANSWERED, self.Status.CLOSED}
