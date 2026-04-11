from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('core', '0010_proposal_is_resent_proposal_original_proposal_and_more'),
    ]
    operations = [
        migrations.AddField(
            model_name='inspection',
            name='is_approved_by_exhibitor',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='inspection',
            name='work_submission',
            field=models.FileField(blank=True, null=True, upload_to='inspection_work/'),
        ),
        migrations.AddField(
            model_name='user',
            name='bank_account_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='bank_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='ifsc_code',
            field=models.CharField(blank=True, max_length=11, null=True),
        ),
    ]