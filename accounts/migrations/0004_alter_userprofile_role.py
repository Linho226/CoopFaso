from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_userprofile_cooperative'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='role',
            field=models.CharField(
                choices=[
                    ('ADMIN', 'Administrateur'),
                    ('COOPERATIVE_MANAGER', 'Responsable de cooperative'),
                    ('FARMER', 'Agriculteur'),
                    ('BUYER', 'Acheteur'),
                ],
                default='BUYER',
                max_length=32,
            ),
        ),
    ]
