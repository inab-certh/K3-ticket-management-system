# Management command to populate geography data
# records/management/commands/populate_geography.py

from django.core.management.base import BaseCommand
from records.models import Region, RegionalUnit, Municipality
import csv
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Populate Greek geography data from Kallikratis structure'

    def handle(self, *args, **options):
        self.stdout.write('Populating Greek geography data...')
        
        # Create regions (13 main regions)
        csv_file = os.path.join(settings.BASE_DIR, 'municipality_data.csv')
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
            return
        
        # Track created objects to avoid duplicates
        regions_created = set()
        units_created = set()
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    # Skip header row (aa column)
                    if row['aa'] == 'aa':
                        continue
                        
                    municipality_name = row['Δήμος (σχ. Καλλικράτης)']
                    unit_name = row['Περιφεριακή Ενότητα']
                    region_code = row['Περιφέρεια']
                    sort_order = int(row['#'])
                    
                    # Create Region if not exists
                    if region_code not in regions_created:
                        # Map region codes to full names
                        region_names = {
                            'ΑΝ. ΜΑΚ.-ΘΡΑΚΗΣ': 'Ανατολική Μακεδονία-Θράκη',
                            'ΚΕΝ. ΜΑΚΕΔΟΝΙΑΣ': 'Κεντρική Μακεδονία',
                            'ΔΥΤ. ΜΑΚΕΔΟΝΙΑΣ': 'Δυτική Μακεδονία',
                            'ΗΠΕΙΡΟΥ': 'Ήπειρος',
                            'ΘΕΣΣΑΛΙΑΣ': 'Θεσσαλία',
                            'ΣΤ. ΕΛΛΑΔΑΣ': 'Στερεά Ελλάδα',
                            'ΙΟΝΙΩΝ ΝΗΣΩΝ': 'Ιόνια Νησιά',
                            'ΔΥΤ. ΕΛΛΑΔΑΣ': 'Δυτική Ελλάδα',
                            'ΠΕΛΟΠΟΝΝΗΣΟΥ': 'Πελοπόννησος',
                            'ΑΤΤΙΚΗΣ': 'Αττική',
                            'ΒΟΡ. ΑΙΓΑΙΟΥ': 'Βόρειο Αιγαίο',
                            'ΝΟΤ. ΑΙΓΑΙΟΥ': 'Νότιο Αιγαίο',
                            'ΚΡΗΤΗΣ': 'Κρήτη',
                        }
                        
                        region_full_name = region_names.get(region_code, region_code)
                        
                        region, created = Region.objects.get_or_create(
                            code=region_code,
                            defaults={
                                'name': region_full_name, 
                                'sort_order': sort_order
                            }
                        )
                        
                        if created:
                            self.stdout.write(f"Created region: {region}")
                        
                        regions_created.add(region_code)
                    
                    # Get the region
                    region = Region.objects.get(code=region_code)
                    
                    # Create Regional Unit if not exists
                    unit_key = f"{region_code}_{unit_name}"
                    if unit_key not in units_created:
                        unit, created = RegionalUnit.objects.get_or_create(
                            region=region,
                            name=unit_name,
                            defaults={'sort_order': 1}  # You can adjust this if needed
                        )
                        
                        if created:
                            self.stdout.write(f"Created regional unit: {unit}")
                        
                        units_created.add(unit_key)
                    
                    # Get the regional unit
                    unit = RegionalUnit.objects.get(region=region, name=unit_name)
                    
                    # Create Municipality
                    municipality, created = Municipality.objects.get_or_create(
                        regional_unit=unit,
                        name=municipality_name,
                        defaults={'sort_order': int(row['aa'])}  # Use the aa column as sort order
                    )
                    
                    if created:
                        self.stdout.write(f"Created municipality: {municipality}")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading CSV file: {e}')
            )
            return
        
        # Print summary
        total_regions = Region.objects.count()
        total_units = RegionalUnit.objects.count()
        total_municipalities = Municipality.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated geography data!\n'
                f'Regions: {total_regions}\n'
                f'Regional Units: {total_units}\n'
                f'Municipalities: {total_municipalities}'
            )
        )