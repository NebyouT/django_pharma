from django.core.management.base import BaseCommand
from pharmacy.models import Role, PharmacyUser

class Command(BaseCommand):
    help = 'Creates initial roles and assigns admin role to superuser'

    def handle(self, *args, **kwargs):
        # Create roles
        roles = [
            ('admin', 'Administrator with full access'),
            ('pharmacist', 'Pharmacist with medicine management access'),
            ('cashier', 'Cashier with sales access'),
            ('inventory', 'Inventory manager with stock management access'),
        ]

        created_roles = []
        for role_name, description in roles:
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={'description': description}
            )
            created_roles.append(role)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created role: {role_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Role already exists: {role_name}'))

        # Assign admin role to superuser
        if created_roles:
            admin_role = Role.objects.get(name='admin')
            superusers = PharmacyUser.objects.filter(is_superuser=True, role__isnull=True)
            for superuser in superusers:
                superuser.role = admin_role
                superuser.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Assigned admin role to superuser: {superuser.username}')
                )
