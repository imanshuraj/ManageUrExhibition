
import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_project_is_paid'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='call_type',
            field=models.CharField(blank=True, choices=[('AUDIO', 'Audio'), ('VIDEO', 'Video')], max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='chat_images/'),
        ),
        migrations.AlterField(
            model_name='jobapplication',
            name='resume',
            field=models.FileField(upload_to=core.models.job_application_upload_path),
        ),
    ]
