from django.db import migrations

def create_default_centers(apps, schema_editor):
    Center = apps.get_model('records', 'Center')
    
    centers = [
        {'name': 'ΑΘΗΝΑ', 'code': 'ATH', 'is_active': True},
        {'name': 'ΘΕΣΣΑΛΟΝΙΚΗ', 'code': 'THE', 'is_active': True},
    ]
    
    for center_data in centers:
        Center.objects.get_or_create(
            name=center_data['name'],
            defaults=center_data
        )

def remove_default_centers(apps, schema_editor):
    Center = apps.get_model('records', 'Center')
    Center.objects.filter(name__in=['ΑΘΗΝΑ', 'ΘΕΣΣΑΛΟΝΙΚΗ']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('records', '0005_alter_person_structure'),
    ]

    operations = [
        migrations.RunPython(create_default_centers, remove_default_centers),
    ]