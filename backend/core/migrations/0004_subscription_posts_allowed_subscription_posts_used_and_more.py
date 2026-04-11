from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_subscription'),
    ]
    operations = [
        migrations.AddField(
            model_name='subscription',
            name='posts_allowed',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='subscription',
            name='posts_used',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='plan_name',
            field=models.CharField(max_length=100),
        ),
    ]