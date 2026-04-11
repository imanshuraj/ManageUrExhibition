from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('core', '0011_inspection_is_approved_by_exhibitor_and_more'),
    ]
    operations = [
        migrations.AddField(
            model_name='project',
            name='is_paid',
            field=models.BooleanField(default=False),
        ),
    ]