from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_admin(apps, schema_editor):
    User = apps.get_model('core', 'User')
    if not User.objects.filter(username='admin').exists():
        User.objects.create(
            username='admin',
            email='admin@manageurexhibition.in',
            password=make_password('Admin@123'),
            is_staff=True,
            is_superuser=True,
            role='OWNER'
        )

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0017_alter_user_adhar_number_and_more'),
    ]
    operations = [
        migrations.RunPython(create_admin),
    ]
