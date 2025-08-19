from django.core.management.base import BaseCommand
from records.models import RequestTag, RequestStatus, RequestCategory, RequestType

class Command(BaseCommand):
    help = 'Populate request-related data'
    
    def handle(self, *args, **options):
        self.stdout.write('Populating request data...')
        
        # Request statuses - matching your model fields
        statuses = [
            ('new', 'Νέο', 'New', True, 1, False, False, True, '#007bff'),
            ('in_progress', 'Σε εξέλιξη', 'In Progress', True, 2, False, False, True, '#ffc107'),
            ('pending_beneficiary', 'Εκκρεμεί απάντηση ωφελούμενου', 'Pending Beneficiary', True, 3, True, True, True, '#fd7e14'),
            ('pending_external', 'Εκκρεμεί απάντηση φορέα', 'Pending External', True, 4, True, True, True, '#e83e8c'),
            ('completed', 'Ολοκληρώθηκε', 'Completed', True, 5, True, False, False, '#28a745'),
            ('cancelled', 'Διακόπηκε', 'Cancelled', True, 6, True, False, False, '#dc3545'),
        ]
        
        for code, name, name_en, is_active, sort_order, is_closed, is_pending, requires_action, color_code in statuses:
            status, created = RequestStatus.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'name_en': name_en,
                    'is_active': is_active,
                    'sort_order': sort_order,
                    'is_closed': is_closed,
                    'is_pending': is_pending,
                    'requires_action': requires_action,
                    'color_code': color_code,
                    'notes': ''
                }
            )
            if created:
                self.stdout.write(f'Created status: {status}')
        
        # Request tags (keep your existing tags_data)
        tags_data = [
            # ΚΕΠΑ related
            ('Δημιουργία Φακέλου ΚΕΠΑ', 'kepa', 'ΚΕΠΑ διαδικασίες', 7, True, True),
            ('Ενημέρωση Διαδικασίας ΚΕΠΑ', 'kepa', 'Ενημέρωση για ΚΕΠΑ', 3, False, False),
            ('Παρακολούθηση Φακέλου ΚΕΠΑ', 'kepa', 'Παρακολούθηση ΚΕΠΑ', 14, False, True),
            
            # Benefits
            ('Απαλλαγές/Παροχές', 'benefits', 'Φορολογικές απαλλαγές', 14, True, True),
            ('Ενημέρωση για Επιδόματα', 'benefits', 'Πληροφορίες επιδομάτων', 3, False, False),
            ('Επίδομα Αεροθεραπείας', 'benefits', 'Αίτηση επιδόματος', 21, True, True),
            
            # Medical
            ('Εύρεση Νοσοκομείου', 'medical', 'Βοήθεια εύρεσης νοσοκομείου', 1, False, True),
            ('Μετεγχειρητική Φροντίδα', 'medical', 'Υπηρεσίες φροντίδας', 30, False, True),
            ('Ψυχολογική Υποστήριξη', 'psychosocial', 'Ψυχολογική βοήθεια', 7, False, True),
            
            # Transport
            ('Έξοδα Μετακίνησης', 'transport', 'Αποζημίωση μετακίνησης', 14, True, True),
            ('Κάρτα ΟΑΣΑ', 'transport', 'Δωρεάν μεταφορά', 7, True, False),
            
            # Work related
            ('Εργασιακά Δικαιώματα', 'work', 'Πληροφορίες εργασίας', 7, False, False),
            ('Άδειες Εργασίας', 'work', 'Ειδικές άδειες', 3, False, False),
            
            # Accommodation
            ('Δωρεάν Φιλοξενία', 'accommodation', 'Φιλοξενία για θεραπείες', 7, False, True),
            ('Κατ\'οίκον Φροντίδα', 'accommodation', 'Φροντίδα στο σπίτι', 14, False, True),
            
            # Financial
            ('Οικονομική Ενίσχυση', 'financial', 'Οικονομική βοήθεια', 21, True, True),
            ('Έξοδα Κηδείας', 'financial', 'Αποζημίωση κηδείας', 3, True, False),
            
            # Education
            ('Εισαγωγή Τριτοβάθμια', 'education', 'Ειδική εισαγωγή', 30, True, True),
        ]
        
        for name, category, description, duration, requires_docs, requires_contact in tags_data:
            tag, created = RequestTag.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'description': description,
                    'estimated_duration_days': duration,
                    'requires_documents': requires_docs,
                    'requires_external_contact': requires_contact,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created tag: {tag}')
        
        self.stdout.write(self.style.SUCCESS('Request data populated!'))