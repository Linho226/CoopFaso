from django.conf import settings
from django.db import migrations


def create_profiles(apps, schema_editor):
    user_model = apps.get_model(settings.AUTH_USER_MODEL)
    user_profile = apps.get_model('accounts', 'UserProfile')
    for user in user_model.objects.all():
        user_profile.objects.get_or_create(user_id=user.pk)


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_profiles, migrations.RunPython.noop),
    ]
