from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('core', '0007_inspection_vendor_rating_and_more'),
    ]
    operations = [
        migrations.AddField(
            model_name='user',
            name='emp_id',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]