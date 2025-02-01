from django.core.management.base import BaseCommand
from pharmacy.models import Role

class Command(BaseCommand):
    help = 'Sets up initial roles in the system'

    def handle(self, *args, **kwargs):
        roles = [
            ('admin', 'Administrator with full system access'),
            ('pharmacist', 'Pharmacist with medicine management access'),
            ('cashier', 'Cashier with sales management access'),
        ]
        
        for name, description in roles:
            Role.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully created roles'))
