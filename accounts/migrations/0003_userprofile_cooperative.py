from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_create_profiles_for_existing_users'),
        ('cooperatives', '0002_cooperative_description_cooperative_is_public_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='cooperative',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='user_profiles',
                to='cooperatives.cooperative',
                verbose_name='cooperative rattachee',
            ),
        ),
    ]
