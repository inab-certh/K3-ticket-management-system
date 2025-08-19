from django.core.management.base import BaseCommand
from records.models import Center, ExternalOrganization

class Command(BaseCommand):
    help = 'Populate organization data'

    def handle(self, *args, **options):
        self.stdout.write('Populating organization data...')
        
        # K3 Centers
        centers = [
            ('K3 Αθήνα', 'Κεντρικό γραφείο Αθήνας', '210-1234567', 'athens@k3.gr'),
            ('K3 Θεσσαλονίκη', 'Παράρτημα Θεσσαλονίκης', '2310-123456', 'thessaloniki@k3.gr'),
        ]
        
        for name, address, phone, email in centers:
            center, created = Center.objects.get_or_create(
                name=name,
                defaults={
                    'address': address,
                    'phone': phone,
                    'email': email,
                }
            )
            if created:
                self.stdout.write(f'Created center: {center}')
        
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