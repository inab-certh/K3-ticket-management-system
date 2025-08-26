# Enhanced records/management/commands/populate_request_data.py

from django.core.management.base import BaseCommand
from records.models import RequestTag, RequestStatus, RequestCategory, RequestType

class Command(BaseCommand):
    help = 'Populate request-related data with comprehensive Excel data'
    
    def handle(self, *args, **options):
        self.stdout.write('Populating comprehensive request data...')
        
        # Enhanced categories based on your Excel analysis
        main_categories = [
            ('kepa', 'ΚΕΠΑ', 'Κέντρα Πιστοποίησης Αναπηρίας'),
            ('benefits', 'Επιδόματα/Παροχές', 'Κοινωνικά επιδόματα και παροχές'),
            ('medical', 'Ιατρικές Υπηρεσίες', 'Ιατρική φροντίδα και υπηρεσίες'),
            ('transport', 'Μετακίνηση', 'Μέσα μεταφοράς και αποζημιώσεις'),
            ('accommodation', 'Φιλοξενία', 'Υπηρεσίες φιλοξενίας και κατοικίας'),
            ('work', 'Εργασιακά', 'Εργασιακά δικαιώματα και υπηρεσίες'),
            ('education', 'Εκπαίδευση', 'Εκπαιδευτικές υπηρεσίες και εισαγωγές'),
            ('financial', 'Οικονομική Υποστήριξη', 'Οικονομική βοήθεια και αποζημιώσεις'),
            ('psychosocial', 'Ψυχοκοινωνική Υποστήριξη', 'Ψυχολογική και κοινωνική υποστήριξη'),
            ('administrative', 'Διοικητικές Διαδικασίες', 'Γραφειοκρατικές διαδικασίες'),
            ('disability', 'Αναπηρία', 'Υπηρεσίες για άτομα με αναπηρία'),
            ('other', 'Άλλα', 'Άλλες κατηγορίες αιτημάτων'),
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

        # Complete request tags from your Excel data
        comprehensive_tags_data = [
            # ΚΕΠΑ (most frequent in your data)
            ('Δημιουργία φακέλου ΚΕΠΑ', 'kepa', 'Δημιουργία νέου φακέλου στο ΚΕΠΑ', 30, True, True, 1),
            ('Δημιουργία/Ενημέρωση Φακέλου ΚΕΠΑ', 'kepa', 'Δημιουργία ή ενημέρωση φακέλου ΚΕΠΑ', 25, True, True, 2),
            ('Ενημέρωση Φακέλου ΚΕΠΑ', 'kepa', 'Ενημέρωση υπάρχοντος φακέλου', 10, False, True, 3),
            ('Βήματα ΚΕΠΑ', 'kepa', 'Ενημέρωση για διαδικασία ΚΕΠΑ', 5, False, False, 4),
            ('Διαδικασία ΚΕΠΑ', 'kepa', 'Πληροφορίες διαδικασίας ΚΕΠΑ', 5, False, False, 5),
            ('Πορεία φακέλου ΚΕΠΑ', 'kepa', 'Παρακολούθηση πορείας φακέλου', 7, False, True, 6),
            ('Αίτηση Επιδείνωσης ΚΕΠΑ', 'kepa', 'Αίτηση επιδείνωσης κατάστασης', 45, True, True, 7),
            ('Αίτηση Παράτασης', 'kepa', 'Παράταση ισχύος ΚΕΠΑ', 30, True, True, 8),
            ('Ισχύ Επ΄αορίστου ΚΕΠΑ', 'kepa', 'Αίτηση για ισχύ επ\' αορίστου', 60, True, True, 9),

            # Απαλλαγές/Παροχές (very common)
            ('Απαλλαγές-Παροχές', 'benefits', 'Φορολογικές απαλλαγές και παροχές ΑΜΕΑ', 20, True, True, 10),
            ('Απαλλαγές/Παροχές', 'benefits', 'Απαλλαγές και παροχές', 20, True, True, 11),
            ('Δικαιώματα-Απαλλαγές/Παροχές', 'benefits', 'Ενημέρωση δικαιωμάτων και απαλλαγών', 15, True, True, 12),
            ('Παροχές μέσω ΕΟΠΥΥ', 'benefits', 'Παροχές μέσω ΕΟΠΥΥ', 15, True, True, 13),
            ('Επιδόματα', 'benefits', 'Κοινωνικά επιδόματα', 25, True, True, 14),
            ('Ενημέρωση για Επιδόματα', 'benefits', 'Πληροφορίες για διαθέσιμα επιδόματα', 5, False, False, 15),
            ('Επίδομα Αεροθεραπείας', 'benefits', 'Επίδομα για αεροθεραπεία', 30, True, True, 16),
            ('Επίδομα ΟΠΕΚΑ', 'benefits', 'Επίδομα παιδιού ΟΠΕΚΑ', 20, True, True, 17),
            ('Επίδομα ετέρου προσώπου', 'benefits', 'Επίδομα για φροντιστή', 25, True, True, 18),
            ('Επίδομα ανεργίας ταυτόχρονα με σύνταξη αναπηρίας', 'benefits', 'Συνδυασμός επιδομάτων', 30, True, True, 19),

            # Μετακίνηση/Μεταφορά
            ('Έξοδα Μετακίνησης', 'transport', 'Αποζημίωση εξόδων μετακίνησης', 15, True, False, 20),
            ('Κάρτα ΟΑΣΑ', 'transport', 'Ειδική κάρτα ΜΜΜ για ΑΜΕΑ', 10, True, False, 21),
            ('Κάρτα Αναπηρίας', 'transport', 'Κάρτα αναπηρίας για μεταφορά', 15, True, False, 22),

            # Φιλοξενία
            ('Δομή Φιλοξενίας', 'accommodation', 'Φιλοξενία σε ειδική δομή', 30, True, True, 23),
            ('Δωρεάν Φιλοξενεία για Θεραπείες', 'accommodation', 'Φιλοξενία κατά τη διάρκεια θεραπειών', 20, True, True, 24),
            ('Δομές Φιλοξενίας', 'accommodation', 'Ειδικές δομές φιλοξενίας', 25, True, True, 25),

            # Εκπαίδευση
            ('Εισαγωγή στην Τριτοβάθμια', 'education', 'Ειδικές θέσεις τριτοβάθμιας', 30, True, True, 26),
            ('Εισαγωγή στην 3βάθμια εκπαίδευση', 'education', 'Εισαγωγή στην τριτοβάθμια', 30, True, True, 27),
            ('Μοριοδότηση για Τριτοβάθμια', 'education', 'Μόρια για πανεπιστήμιο', 20, True, True, 28),
            ('Ενημέρωση για εκπαιδευτικά θέματα', 'education', 'Εκπαιδευτικές πληροφορίες', 5, False, False, 29),

            # Ιατρικά/Φάρμακα
            ('Αναζήτηση Φαρμάκων', 'medical', 'Εύρεση και πρόσβαση σε φάρμακα', 10, False, True, 30),
            ('Έγκριση Φαρμάκου ΕΟΦ', 'medical', 'Έγκριση φαρμάκου από ΕΟΦ', 45, True, True, 31),
            ('Εξετάσεις για Βιοδείκτες', 'medical', 'Ειδικές ιατρικές εξετάσεις', 15, True, True, 32),
            ('Εύρεση Νοσοκομείου', 'medical', 'Εύρεση κατάλληλου νοσοκομείου', 5, False, True, 33),
            ('Κλινικές Εξωτερικού', 'medical', 'Παραπομπή σε κλινικές εξωτερικού', 60, True, True, 34),
            ('Νοσοκομείο για μεταγγίσεις αίματος', 'medical', 'Εύρεση νοσοκομείου για μεταγγίσεις', 7, False, True, 35),
            ('Διαδικασίες εντός του Νοσοκομείου', 'administrative', 'Βοήθεια με νοσοκομειακές διαδικασίες', 10, False, True, 36),
            ('Βοήθεια στο σπίτι', 'medical', 'Κατ\' οίκον φροντίδα', 15, True, True, 37),
            ('Κατ\'οίκον φροντίδα', 'medical', 'Φροντίδα στο σπίτι', 15, True, True, 38),
            ('Μετεγχειρητική φροντίδα', 'medical', 'Φροντίδα μετά από επέμβαση', 20, True, True, 39),
            ('Ανακουφιστική Φροντίδα', 'medical', 'Παρηγορητική φροντίδα', 20, True, True, 40),
            ('Υπηρεσίες Ανακουφιστικής Φροντίδας', 'medical', 'Ανακουφιστική φροντίδα', 20, True, True, 41),
            ('Παρηγορητική Φροντίδα', 'medical', 'Φροντίδα τέλους ζωής', 15, True, True, 42),
            ('Φυσικοθεραπευτής', 'medical', 'Υπηρεσίες φυσικοθεραπείας', 10, True, True, 43),
            ('Διατροφικό πλάνο', 'medical', 'Συμβουλευτική διατροφής', 5, False, True, 44),
            ('Κρύα Καπέλα', 'medical', 'Εξοπλισμός για χημειοθεραπεία', 3, False, False, 45),
            ('Περούκα', 'medical', 'Πρόσθεση μαλλιών', 7, True, False, 46),
            ('Αιματολογικές εξετάσεις', 'medical', 'Εργαστηριακές εξετάσεις αίματος', 7, True, True, 47),
            ('Επέμβαση Λέιζερ', 'medical', 'Λέιζερ θεραπεία', 15, True, True, 48),

            # Ψυχοκοινωνική Υποστήριξη
            ('Ψυχολογική Υποστήριξη', 'psychosocial', 'Ψυχολογική βοήθεια και συμβουλευτική', 30, True, True, 49),
            ('Παραπομπή για ψυχολογική υποστήριξη', 'psychosocial', 'Παραπομπή σε ψυχολόγο', 10, False, True, 50),

            # Εργασιακά
            ('Εργασιακά Δικαιώματα', 'work', 'Δικαιώματα στον εργασιακό χώρο', 15, True, True, 51),
            ('Θέση ΑΜΕΑ', 'work', 'Ειδικές θέσεις εργασίας για ΑΜΕΑ', 45, True, True, 52),
            ('Άδειες Εργασίας', 'work', 'Ειδικές άδειες για εργαζόμενους', 10, True, False, 53),
            ('Άδειες στον ιδιωτικό τομέα', 'work', 'Άδειες ιδιωτικού τομέα', 7, True, False, 54),
            ('Άδειες Δημοσίου', 'work', 'Άδειες δημοσίου τομέα', 7, True, False, 55),
            ('Άδεια για εξετάσεις', 'work', 'Ειδική άδεια για ιατρικές εξετάσεις', 3, True, False, 56),
            ('Άδεια παραμονής', 'work', 'Άδεια για παραμονή με ασθενή', 5, True, False, 57),
            ('Αίτηση ανεργίας σε επεξεργασία', 'work', 'Διεκπεραίωση αίτησης ανεργίας', 15, True, True, 58),

            # Οικονομική Υποστήριξη
            ('Οικονομική Ενίσχυση', 'financial', 'Οικονομική υποστήριξη', 30, True, True, 59),
            ('Έξοδα Κηδείας', 'financial', 'Επιστροφή εξόδων κηδείας', 15, True, False, 60),
            ('Αποζημίωση Αναλώσιμων', 'financial', 'Αποζημίωση ιατρικών αναλώσιμων', 20, True, False, 61),
            ('Αποζημίωση ασφαλιστικής', 'financial', 'Ασφαλιστική αποζημίωση', 30, True, True, 62),
            ('Παροχή Φαγητού', 'financial', 'Διανομή τροφίμων', 1, False, True, 63),
            ('Ρεύμα, Νερό, Τρόφιμα', 'financial', 'Βοήθεια με βασικές ανάγκες', 7, True, True, 64),

            # Συντάξεις
            ('Σύνταξη Αναπηρίας', 'benefits', 'Αίτηση σύνταξης αναπηρίας', 60, True, True, 65),
            ('Αναπηρική Σύνταξη', 'benefits', 'Σύνταξη λόγω αναπηρίας', 60, True, True, 66),
            ('Υποστήριξη για κοινωνικές παροχές', 'benefits', 'Βοήθεια για κοινωνικές παροχές', 20, True, True, 67),

            # Διοικητικά/Ενημέρωση
            ('Ενημέρωση', 'administrative', 'Γενική ενημέρωση', 5, False, False, 68),
            ('Ενημέρωση δικαιωμάτων', 'administrative', 'Πληροφορίες για δικαιώματα', 10, False, False, 69),
            ('Ενημέρωση για εισηγητικό φάκελο', 'administrative', 'Πληροφορίες εισηγητικού φακέλου', 5, False, False, 70),
            ('Συνταγογράφηση σκιαγραφικού', 'medical', 'Συνταγή για σκιαγραφικό υλικό', 3, True, True, 71),
            ('Εννιαιός πίνακας προσδιορισμού αναπηρίας', 'disability', 'Πίνακας αναπηρίας', 15, True, True, 72),
            ('Αλλαγή διεύθυνσης επιτροπής', 'administrative', 'Μεταφορά σε άλλη επιτροπή', 10, True, True, 73),
            ('Έκπτωση σε ταυτοποίηση αυθαιρέτων', 'administrative', 'Έκπτωση για ακίνητα', 30, True, True, 74),

            # Άλλα/Ειδικά
            ('Αποκλειστική', 'other', 'Αποκλειστική περίπτωση', 15, True, True, 75),
            ('Εξέταση', 'medical', 'Γενική ιατρική εξέταση', 7, True, True, 76),
            ('Άλλο', 'other', 'Άλλες κατηγορίες', 15, False, False, 99),
        ]
        
        for name, category, description, duration, requires_docs, requires_contact, priority in comprehensive_tags_data:
            tag, created = RequestTag.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'description': description,
                    'estimated_duration_days': duration,
                    'requires_documents': requires_docs,
                    'requires_external_contact': requires_contact,
                    'is_active': True,
                    #'priority_order': priority,
                }
            )
            if created:
                self.stdout.write(f'Created tag: {tag}')
        
        # Keep your existing status definitions - they look good
        statuses = [
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
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated {len(comprehensive_tags_data)} request tags, '
                f'{len(main_categories)} categories, and {len(statuses)} statuses!'
            )
        )