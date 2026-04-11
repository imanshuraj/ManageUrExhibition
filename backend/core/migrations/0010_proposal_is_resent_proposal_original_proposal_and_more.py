import django.db.models.deletion
from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('core', '0009_user_adhar_number'),
    ]
    operations = [
        migrations.AddField(
            model_name='proposal',
            name='is_resent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='proposal',
            name='original_proposal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resent_versions', to='core.proposal'),
        ),
        migrations.AddField(
            model_name='proposal',
            name='resent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='proposal',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected'), ('RESENT', 'Resent Quotation')], default='PENDING', max_length=20),
        ),
    ]