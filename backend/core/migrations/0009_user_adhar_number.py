from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('core', '0008_user_emp_id'),
    ]
    operations = [
        migrations.AddField(
            model_name='user',
            name='adhar_number',
            field=models.CharField(blank=True, max_length=12, null=True, unique=True),
        ),
    ]