from django.core.management.base import BaseCommand
from core.models import User
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Sets the admin password to a specific value and ensures the user exists'

    def handle(self, *args, **options):
        new_pw = '7549614028Aa@'
        username = 'admin'
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'is_staff': True,
                'is_superuser': True,
                'email': 'admin@manageurexhibition.in',
                'role': 'ADMIN'
            }
        )
        
        user.set_password(new_pw)
        user.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser "{username}" with the requested password.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully updated password for user "{username}".'))
