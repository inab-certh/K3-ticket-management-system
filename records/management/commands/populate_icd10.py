# Management command to populate ICD-10 data
# records/management/commands/populate_icd10.py

import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from records.models import ICD10Category, ICD10Subcategory, ICD10Code

class Command(BaseCommand):
    help = 'Populate ICD-10 data from CSV file'

    def handle(self, *args, **options):
        self.stdout.write('Populating ICD-10 data from CSV...')
        
        # Path to your CSV file (in project root)
        csv_file = os.path.join(settings.BASE_DIR, 'icd10_data.csv')
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
            return
        
        # Track created objects to avoid duplicates
        categories_created = {}
        subcategories_created = {}
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    category_code = row['category_code_range']
                    category_name = row['category_name']
                    subcategory_name = row['subcategory_name']
                    icd10_code = row['icd10_code']
                    icd10_label = row['icd10_label']
                    is_common = row['is_common'].lower() == 'true'
                    
                    # Create Category if not exists
                    if category_code not in categories_created:
                        # Determine category properties
                        is_cancer_related = True  # All our categories are cancer-related
                        sort_order = 1
                        if category_code == 'C00-C97':
                            sort_order = 1
                        elif category_code == 'D10-D36':
                            sort_order = 2
                        elif category_code == 'D37-D48':
                            sort_order = 3
                        elif category_code == 'D00-D09':
                            sort_order = 4
                        
                        category, created = ICD10Category.objects.get_or_create(
                            code_range=category_code,
                            defaults={
                                'name': category_name,
                                'sort_order': sort_order,
                                'is_cancer_related': is_cancer_related
                            }
                        )
                        
                        if created:
                            self.stdout.write(f"Created category: {category}")
                        
                        categories_created[category_code] = category
                    else:
                        category = categories_created[category_code]
                    
                    # Create Subcategory if not exists
                    subcategory_key = f"{category_code}_{subcategory_name}"
                    if subcategory_key not in subcategories_created:
                        subcategory, created = ICD10Subcategory.objects.get_or_create(
                            category=category,
                            name=subcategory_name,
                            defaults={
                                'description': f'Subcategory for {subcategory_name}',
                                'sort_order': len(subcategories_created) + 1
                            }
                        )
                        
                        if created:
                            self.stdout.write(f"Created subcategory: {subcategory}")
                        
                        subcategories_created[subcategory_key] = subcategory
                    else:
                        subcategory = subcategories_created[subcategory_key]
                    
                    # Create ICD10 Code
                    icd_code, created = ICD10Code.objects.get_or_create(
                        code=icd10_code,
                        defaults={
                            'label': icd10_label,
                            'category': category,
                            'subcategory': subcategory,
                            'is_common': is_common,
                            'is_active': True
                        }
                    )
                    
                    if created:
                        self.stdout.write(f"Created ICD code: {icd_code}")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading CSV file: {e}')
            )
            return
        
        # Print summary
        total_categories = ICD10Category.objects.count()
        total_subcategories = ICD10Subcategory.objects.count()
        total_codes = ICD10Code.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated ICD-10 data!\n'
                f'Categories: {total_categories}\n'
                f'Subcategories: {total_subcategories}\n'
                f'ICD10 Codes: {total_codes}'
            )
        )
        
        # Show some statistics
        self.stdout.write('\nBreakdown by category:')
        for category in ICD10Category.objects.all():
            code_count = ICD10Code.objects.filter(category=category).count()
            subcategory_count = ICD10Subcategory.objects.filter(category=category).count()
            self.stdout.write(
                f'  {category.name}: {subcategory_count} subcategories, {code_count} codes'
            )