from django.core.management.base import BaseCommand
from records.models import RequestTag, RequestStatus, RequestCategory, RequestType

class Command(BaseCommand):
    help = 'Populate request-related data'
    
    def handle(self, *args, **options):
        self.stdout.write('Populating request data...')
        
        main_categories = [
            ('drug_search', 'Αναζήτηση Φαρμάκων', 'Βοήθεια εύρεσης και πρόσβασης σε φάρμακα'),
            ('exemptions_benefits', 'Απαλλαγές/Παροχές', 'Φορολογικές απαλλαγές και παροχές'),
            ('consumables_reimbursement', 'Αποζημίωση Αναλώσιμων', 'Αποζημίωση ιατρικών αναλώσιμων'),
            ('kepa_file', 'Δημιουργία/Ενημέρωση Φακέλου ΚΕΠΑ', 'Διαδικασίες ΚΕΠΑ'),
            ('hospital_procedures', 'Διαδικασίες εντός του Νοσοκομείου', 'Νοσοκομειακές διαδικασίες'),
            ('free_accommodation', 'Δωρεάν Φιλοξενεία για Θεραπείες', 'Φιλοξενία κατά τη διάρκεια θεραπειών'),
            ('university_admission', 'Εισαγωγή στην 3βάθμια εκπαίδευση', 'Ειδική εισαγωγή στην τριτοβάθμια'),
            ('assessment_file_info', 'Ενημέρωση για εισηγητικό φάκελο', 'Πληροφορίες για εισηγητικό φάκελο'),
            ('benefits_info', 'Ενημέρωση για Επιδόματα', 'Πληροφορίες για επιδόματα'),
            ('biomarker_tests', 'Εξετάσεις για Βιοδείκτες', 'Εργαστηριακές εξετάσεις'),
            ('travel_expenses', 'Έξοδα Μετακίνησης', 'Αποζημίωση εξόδων μετακίνησης'),
            ('employment_rights', 'Εργασιακά Δικαιώματα', 'Δικαιώματα στον εργασιακό χώρο'),
            ('home_care', 'Κατ\'οίκον φροντίδα', 'Υπηρεσίες φροντίδας στο σπίτι'),
            ('international_clinics', 'Κλινικές Εξωτερικού', 'Πρόσβαση σε κλινικές εξωτερικού'),
            ('financial_support', 'Οικονομική Ενίσχυση', 'Οικονομική υποστήριξη'),
            ('eopyy_benefits', 'Παροχές μέσω ΕΟΠΥΥ', 'Παροχές μέσω ΕΟΠΥΥ'),
            ('palliative_care', 'Υπηρεσίες Ανακουφιστικής Φροντίδας', 'Παρηγορητική φροντίδα'),
            ('psychological_support', 'Ψυχολογική Υποστήριξη', 'Ψυχολογική βοήθεια'),
            ('funeral_expenses', 'Έξοδα Κηδείας', 'Αποζημίωση εξόδων κηδείας'),
            ('other', 'Άλλο', 'Άλλες κατηγορίες αιτημάτων'),
        ]
        
        for code, name, description in main_categories:
            category, created = RequestCategory.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': description,
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'Created category: {category}')
                
        # Request statuses - matching your model fields
        statuses = [
            # code, name, name_en, is_active, sort_order, is_closed, is_pending, requires_action, color_code
            ('recorded', 'Καταγραφή αιτήματος', 'Request Recorded', True, 1, False, False, True, '#6c757d'),
            ('contacting_org', 'Επικοινωνία με φορέα', 'Contacting Organization', True, 2, False, False, True, '#007bff'),
            ('pending_org_response', 'Εκκρεμεί, απάντηση φορέα', 'Pending Organization Response', True, 3, False, True, True, '#e83e8c'),
            ('pending_beneficiary', 'Εκκρεμεί, απάντηση ωφελούμενου', 'Pending Beneficiary Response', True, 4, False, True, True, '#fd7e14'),
            ('pending_notification', 'Εκκρεμεί, κοινοποίηση αποτελέσματος', 'Pending Result Notification', True, 5, False, True, True, '#ffc107'),
            ('completed', 'Ολοκλήρωση', 'Completed', True, 6, True, False, False, '#28a745'),
            ('assessment', 'Αξιολόγηση', 'Assessment', True, 7, False, False, True, '#17a2b8'),
            ('discontinued', 'Διακοπή', 'Discontinued', True, 8, True, False, False, '#dc3545'),
            ('deceased', 'Απεβίωσε', 'Deceased', True, 9, True, False, False, '#343a40'),
            ('other', 'Άλλο', 'Other', True, 10, False, False, True, '#6f42c1'),
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