from pathlib import Path
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from core.models import User
username = "admin"
email = "admin@example.com"
password = "7549614028Aa@"
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password, role=User.Role.ADMIN)
    print(f"Superuser '{username}' created successfully with ADMIN role.")
else:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.role = User.Role.ADMIN
    user.save()
    print(f"User '{username}' updated to ADMIN role successfully.")