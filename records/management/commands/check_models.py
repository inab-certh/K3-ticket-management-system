# records/management/commands/check_models.py
"""
Management command to check if all models are properly set up
Run: python manage.py check_models
"""

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connection

class Command(BaseCommand):
    help = 'Check if all K3 models are properly set up and migrated'

    def handle(self, *args, **options):
        self.stdout.write('Checking K3 models status...\n')
        
        # List of expected models
        expected_models = [
            'Person', 'Insurance', 'Employment', 'ContactPerson',
            'MedicalHistory', 'Neoplasm', 'Therapy', 'Comorbidity',
            'Request', 'RequestTag', 'RequestAttachment',
            'Action', 'ActionAttachment',
            'Center', 'ExternalOrganization', 'Contact',
            'Document', 'DocumentType',
            'ICD10Code', 'ICD10Category', 'ICD10Subcategory',
            'Region', 'RegionalUnit', 'Municipality',
            'RequestType', 'RequestStatus', 'RequestCategory',
            'InsuranceProvider', 'EmploymentStatus', 'TherapyType'
        ]
        
        app_label = 'records'
        
        # Check if models are registered
        self.stdout.write('1. Checking model registration:')
        app = apps.get_app_config(app_label)
        registered_models = [model.__name__ for model in app.get_models()]
        
        missing_models = []
        for model_name in expected_models:
            if model_name in registered_models:
                self.stdout.write(f'   ✓ {model_name}')
            else:
                self.stdout.write(f'   ✗ {model_name} (missing)')
                missing_models.append(model_name)
        
        # Check if tables exist in database
        self.stdout.write('\n2. Checking database tables:')
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = DATABASE() AND table_name LIKE %s
            """, [f'{app_label}_%'])
            existing_tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [f'{app_label}_{model_name.lower()}' for model_name in registered_models]
        
        missing_tables = []
        for table in expected_tables:
            if table in existing_tables:
                self.stdout.write(f'   ✓ {table}')
            else:
                self.stdout.write(f'   ✗ {table} (needs migration)')
                missing_tables.append(table)
        
        # Summary and recommendations
        self.stdout.write('\n' + '='*50)
        if not missing_models and not missing_tables:
            self.stdout.write(self.style.SUCCESS('✅ All models are ready!'))
            self.stdout.write('\nNext steps:')
            self.stdout.write('1. python manage.py populate_geography')
            self.stdout.write('2. python manage.py populate_icd10') 
            self.stdout.write('3. python manage.py populate_lookups')
            self.stdout.write('4. Set up Django Admin')
        else:
            if missing_models:
                self.stdout.write(self.style.ERROR(f'❌ Missing {len(missing_models)} models'))
                self.stdout.write('Run: Check your models/__init__.py imports')
            
            if missing_tables:
                self.stdout.write(self.style.WARNING(f'⚠️  Need to migrate {len(missing_tables)} tables'))
                self.stdout.write('Run: python manage.py makemigrations')
                self.stdout.write('Then: python manage.py migrate')

# Quick setup guide
SETUP_GUIDE = """
# K3 Django Setup Guide

## Step 1: Check Models
python manage.py check_models

## Step 2: Create Migrations (if needed)
python manage.py makemigrations records

## Step 3: Apply Migrations  
python manage.py migrate

## Step 4: Populate Reference Data
python manage.py populate_geography
python manage.py populate_icd10
python manage.py populate_lookups

## Step 5: Create Superuser
python manage.py createsuperuser

## Step 6: Test Admin Interface
python manage.py runserver
# Go to: http://localhost:8000/admin

## Step 7: Import Excel Data
# We'll create an import command next
"""

print(SETUP_GUIDE)