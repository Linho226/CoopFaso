from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_processed_status(apps, schema_editor):
    contact_message = apps.get_model('public_site', 'ContactMessage')
    contact_message.objects.filter(is_processed=True).update(status='CLOSED')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('public_site', '0002_default_public_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactmessage',
            name='admin_reply',
            field=models.TextField(blank=True, verbose_name='reponse'),
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='category',
            field=models.CharField(
                choices=[
                    ('ROLE_REQUEST', 'Demande de role'),
                    ('SUPPORT', 'Assistance technique'),
                    ('ORDER', 'Commande ou paiement'),
                    ('PARTNERSHIP', 'Partenariat'),
                    ('INFORMATION', "Demande d'information"),
                    ('OTHER', 'Autre'),
                ],
                default='INFORMATION',
                max_length=24,
                verbose_name='motif',
            ),
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='processed_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='processed_contact_messages',
                to=settings.AUTH_USER_MODEL,
                verbose_name='traite par',
            ),
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='replied_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='date de reponse'),
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='sender',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='contact_messages',
                to=settings.AUTH_USER_MODEL,
                verbose_name='utilisateur',
            ),
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='status',
            field=models.CharField(
                choices=[
                    ('NEW', 'Nouveau'),
                    ('IN_PROGRESS', 'En cours'),
                    ('ANSWERED', 'Repondu'),
                    ('CLOSED', 'Cloture'),
                ],
                default='NEW',
                max_length=16,
                verbose_name='statut',
            ),
        ),
        migrations.RunPython(migrate_processed_status, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='contactmessage',
            name='is_processed',
        ),
    ]
