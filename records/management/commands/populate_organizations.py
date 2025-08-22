from django.core.management.base import BaseCommand
from records.models import Center, ExternalOrganization

class Command(BaseCommand):
    help = 'Populate organization data'

    def handle(self, *args, **options):
        self.stdout.write('Populating organization data...')
        
        # K3 Centers
        centers = [
            {
                'name': 'ΑΘΗΝΑ',
                'code': '1',
                'address': 'Κωστή Παλαμά 13, 3ος όροφος',
                'municipality': 'ΑΘΗΝΑΙΩΝ',
                'phone': '2105221424',
                'email': 'info@kapa3.gr',
                'is_active': True
            },
            {
                'name': 'ΘΕΣΣΑΛΟΝΙΚΗ',
                'code': '2', 
                'address': 'Θεαγένειο Νοσοκομείο, στην είσοδο',
                'municipality': 'ΘΕΣΣΑΛΟΝΙΚΗΣ',
                'phone': '6982003282',
                'email': None,  # No email provided
                'is_active': True
            },
            {
                'name': 'ΑΛΕΞΑΝΔΡΟΥΠΟΛΗ',
                'code': '3',
                'address': 'Πανεπιστημιακό Νοσοκομείο Αλεξανδρούπολης 1ο κτήριο, 1ος όροφος στην Ογκολογική Κλινική-Βραχεία Νοσηλεία',
                'municipality': 'ΑΛΕΞΑΝΔΡΟΥΠΟΛΗΣ', 
                'phone': '6976599184',
                'email': 'k3alex@kapa3.gr',
                'is_active': True
            },
        ]
        
        for center_data in centers:
            center, created = Center.objects.get_or_create(
                name=center_data['name'],
                defaults={
                    'code': center_data['code'],
                    'address': center_data['address'],
                    'municipality': center_data['municipality'],
                    'phone': center_data['phone'],
                    'email': center_data['email'],
                    'is_active': center_data['is_active'],
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created center: {center.name} (Code: {center.code})')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Center already exists: {center.name}')
                )
        
        # External organizations
        orgs = [
            ('ΕΟΠΥΥ', 'insurance', True),
            ('Νοσοκομείο Αλεξάνδρα', 'hospital', True),
            ('Νοσοκομείο Αγίων Αναργύρων', 'hospital', True),
            ('ΚΕΠΑ Αθήνας', 'ministry', True),
            ('Δήμος Αθηναίων - Κοινωνική Υπηρεσία', 'social_service', True),
        ]
        
        for name, org_type, is_active in orgs:
            org, created = ExternalOrganization.objects.get_or_create(
                name=name,
                defaults={
                    'org_type': org_type,
                    'is_active': is_active,
                }
            )
            if created:
                self.stdout.write(f'Created organization: {org}')
        
        self.stdout.write(self.style.SUCCESS('Organization data populated!'))