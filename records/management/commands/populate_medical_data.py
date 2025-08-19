from django.core.management.base import BaseCommand
from records.models import ICD10Category, ICD10Code, TherapyType, InsuranceProvider, EmploymentStatus

class Command(BaseCommand):
    help = 'Populate medical and insurance data'

    def handle(self, *args, **options):
        self.stdout.write('Populating medical data...')
              
        # Therapy types
        therapies = [
            ('Χημειοθεραπεία', 'systemic', False, 12),
            ('Ακτινοθεραπεία', 'local', False, 6),
            ('Ορμονοθεραπεία', 'systemic', False, 52),
            ('Στοχευμένη Θεραπεία', 'systemic', False, 16),
            ('Ανοσοθεραπεία', 'systemic', False, 24),
            ('Χειρουργείο', 'surgical', True, 1),
        ]
        
        for name, category, requires_hosp, weeks in therapies:
            therapy, created = TherapyType.objects.get_or_create(
                name=name,
                defaults={
                    'therapy_category': category,
                    'requires_hospitalization': requires_hosp,
                    'typical_duration_weeks': weeks,
                }
            )
            if created:
                self.stdout.write(f'Created therapy: {therapy}')
        
        # Insurance providers
        providers = [
            ('ΕΟΠΥΥ', 'public'),
            ('ΙΚΑ', 'public'),
            ('ΟΓΑ', 'public'),  
            ('ΔΗΜΟΣΙΟ', 'public'),
            ('ΤΣΜΕΔΕ', 'special'),
            ('ΟΑΕΕ', 'special'),
            ('ΕΤΑΑ', 'special'),
        ]
        
        for name, provider_type in providers:
            provider, created = InsuranceProvider.objects.get_or_create(
                name=name,
                defaults={'provider_type': provider_type}
            )
            if created:
                self.stdout.write(f'Created insurance provider: {provider}')
        
        # Employment statuses
        emp_statuses = [
            ('Εργαζόμενος/η', False, False),
            ('Άνεργος/η', True, False),
            ('Συνταξιούχος', False, True),
            ('Φοιτητής/τρια', False, False),
            ('Οικιακά', False, False),
        ]
        
        for name, is_unemployed, is_retired in emp_statuses:
            status, created = EmploymentStatus.objects.get_or_create(
                name=name,
                defaults={
                    'is_unemployed': is_unemployed,
                    'is_retired': is_retired,
                }
            )
            if created:
                self.stdout.write(f'Created employment status: {status}')
        
        self.stdout.write(self.style.SUCCESS('Medical data populated!'))