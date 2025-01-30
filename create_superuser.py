from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharmacy_management.settings')
django.setup()

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
