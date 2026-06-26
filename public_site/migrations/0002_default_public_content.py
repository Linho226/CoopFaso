from django.db import migrations


def create_default_content(apps, schema_editor):
    PlatformInfo = apps.get_model('public_site', 'PlatformInfo')
    ProductCategory = apps.get_model('products', 'ProductCategory')

    PlatformInfo.objects.get_or_create(
        name='CoopFaso',
        defaults={
            'headline': 'Connectons les cooperatives, les producteurs et les acheteurs.',
            'presentation': (
                'CoopFaso valorise les produits agricoles locaux, facilite leur '
                'commercialisation et accompagne les acteurs avec des formations pratiques.'
            ),
            'mission': (
                'Renforcer les cooperatives agricoles grace au numerique et favoriser '
                'un acces transparent aux marches.'
            ),
            'address': 'Ouagadougou, Burkina Faso',
        },
    )
    for name in (
        'Cereales',
        'Fruits',
        'Legumes',
        'Oleagineux',
        'Tubercules',
        'Produits transformes',
    ):
        ProductCategory.objects.get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0002_productcategory_product_is_published_and_more'),
        ('public_site', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_content, migrations.RunPython.noop),
    ]
