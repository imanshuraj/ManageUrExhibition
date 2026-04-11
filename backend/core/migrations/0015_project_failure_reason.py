
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_message_is_group_message_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='failure_reason',
            field=models.TextField(blank=True, null=True),
        ),
    ]
