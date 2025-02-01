from django.core.management.base import BaseCommand
from pharmacy.models import Medicine
from datetime import datetime
from django.utils import timezone

class Command(BaseCommand):
    help = 'Import initial medicine data'

    def parse_date(self, date_str):
        if not date_str:
            return None
        
        try:
            # Try standard date format dd/mm/yyyy
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        except ValueError:
            try:
                # Try Excel serial date number format
                excel_epoch = datetime(1899, 12, 30)  # Excel's epoch date
                delta_days = int(date_str)
                return (excel_epoch + timezone.timedelta(days=delta_days)).date()
            except (ValueError, TypeError):
                self.stdout.write(self.style.WARNING(f'Could not parse date: {date_str}'))
                return None

    def handle(self, *args, **kwargs):
        # Data to import
        medicine_data = [
            ('HM-001', 'ACYCLOVIR CAPULES 200MG 10*10', 'STP', 'BF PHARMACETICAL', 20.0, '09624030020', '46023', '14/06/2024', 20.0, '40', '70'),
            ('HM-002', 'ACYCLOVIR 200MG/5ML SUS (LOVRAK)', 'BOT', 'FIROMAY', 3.0, '0011', '30/11/2027', None, 3.0, None, '690'),
            ('HM-003', 'ACYCLOVIR CAPULES 400MG 10*10', 'STP', 'MULU -TIB', None, None, None, None, None, None, None),
            ('HM-004', 'ACYCLOVIR CRAME 5G (FICYC)', 'TUB', 'BF PHARMACETICAL', 5.0, '014', '30/12/2026', None, 1.0, None, '250'),
            ('HM-005', 'ACYCLOVIR CRAME (CORALS)', 'TUB', 'SERHA TRADING', 10.0, 'CA20', '30/04/2027', None, 10.0, None, '190'),
            ('HM-007', 'ACETYLCYSTEINE 100ML (ASIST) MUCOLYTIC', 'BOT', 'MULU -TIB', 5.0, '23195033A', '30/03/2025', None, 2.0, None, '380'),
        ]

        for data in medicine_data:
            if not all([data[0], data[1]]):  # Skip if code or description is missing
                continue

            try:
                # Parse dates
                expiry_date = self.parse_date(data[6])
                receiving_date = self.parse_date(data[7])

                # Create medicine object
                medicine = Medicine(
                    code=data[0],
                    item_description=data[1],
                    unit=data[2] if data[2] else 'piece',
                    received_from=data[3],
                    quantity=float(data[4]) if data[4] else 0,
                    batch_number=data[5],
                    expiry_date=expiry_date if expiry_date else timezone.now().date(),
                    receiving_date=receiving_date if receiving_date else timezone.now().date(),
                    balance=float(data[8]) if data[8] else 0,
                    unit_price=float(data[9]) if data[9] else 0,
                    selling_price=float(data[10]) if data[10] else 0
                )
                medicine.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully imported medicine {data[0]}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to import medicine {data[0]}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Data import completed'))
