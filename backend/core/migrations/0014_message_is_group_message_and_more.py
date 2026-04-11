
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_message_call_type_message_image_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_group_message',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='project',
            name='is_under_failure_review',
            field=models.BooleanField(default=False),
        ),
    ]
