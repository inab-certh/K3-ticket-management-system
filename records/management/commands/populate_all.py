from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Populate all reference data for K3 system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting K3 data population...'))
        
        # Run all population commands in order
        commands = [
            'populate_geography',
            'populate_icd10',
            'populate_request_data', 
            'populate_medical_data',
            'populate_organizations',
        ]
        
        for cmd in commands:
            try:
                call_command(cmd)
                self.stdout.write(f'✅ {cmd} completed successfully')
            except Exception as e:
                self.stdout.write(f'❌ {cmd} failed: {e}')
        
        self.stdout.write(self.style.SUCCESS('🎉 All data populated! Your K3 system is ready!'))
