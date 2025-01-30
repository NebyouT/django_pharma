import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharmacy_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from pharmacy.models import Role

User = get_user_model()

# Create admin role if it doesn't exist
admin_role, created = Role.objects.get_or_create(
    name='admin',
    defaults={'description': 'Administrator with full system access'}
)

# Assign admin role to admin user
admin_user = User.objects.get(username='admin')
admin_user.role = admin_role
admin_user.save()

print("Admin role created and assigned successfully")
