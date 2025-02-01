from django.core.management.base import BaseCommand
from pharmacy.models import Medicine

class Command(BaseCommand):
    help = 'Clears all data from the medicines table'

    def handle(self, *args, **options):
        # Delete all medicine records
        count = Medicine.objects.all().delete()[0]
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} medicines'))
