from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_jobposting_remove_message_image_message_file_and_more'),
    ]
    operations = [
        migrations.AddField(
            model_name='jobapplication',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('REVIEWING', 'Under Review'), ('INTERVIEWING', 'Interview Scheduled'), ('REJECTED', 'Rejected'), ('HIRED', 'Hired')], default='PENDING', max_length=20),
        ),
    ]