from core.models import User
import os

username = 'admin'
email = 'admin@manageurexhibition.in'
password = 'Admin@123' # Change this after your first login!

if not User.objects.filter(username=username).exists():
    print(f"Creating superuser {username}...")
    User.objects.create_superuser(username, email, password)
    print("Superuser created successfully.")
else:
    print(f"Superuser {username} already exists.")
