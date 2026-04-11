import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from core.models import Category
categories = [
    'Booth Design & Construction',
    'Audio & Visual Equipment',
    'Marketing & Promotional Materials',
    'Staffing & Talent',
    'Logistics & Shipping',
    'Catering & Hospitality',
    'Technology & Registration Services'
]
for name in categories:
    Category.objects.get_or_create(name=name)
print("Default categories populated successfully!")