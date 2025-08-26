# Replace your 0011_populate_document_types.py with this corrected version
# This uses only the fields that currently exist in your DocumentType model

from django.db import migrations

def populate_document_types(apps, schema_editor):
    DocumentType = apps.get_model('records', 'DocumentType')
    
    # Define document types using only existing fields (name, description, is_required_for_requests)
    document_types = [
        # Medical/Health Documents (critical & important)
        ('Πιστοποιητικό ΚΕΠΑ', 'Πιστοποιητικό ΚΕΠΑ για αναπηρία', True),
        ('Ανανέωση ΚΕΠΑ', 'Ανανέωση πιστοποιητικού ΚΕΠΑ', True),
        ('Πιστοποιητικό Αναπηρίας', 'Επίσημο πιστοποιητικό αναπηρίας', True),
        ('Ιατρική Γνωμάτευση', 'Ιατρική γνωμάτευση από ειδικό γιατρό', True),
        ('Ιατρικό Ιστορικό', 'Πλήρες ιατρικό ιστορικό του ωφελούμενου', False),
        ('Αποτελέσματα Βιοψίας', 'Αποτελέσματα βιοψίας για νεόπλασμα', False),
        ('Εργαστηριακές Εξετάσεις', 'Αποτελέσματα εργαστηριακών εξετάσεων', False),
        ('Απεικονιστικές Εξετάσεις', 'CT, MRI, ακτινογραφίες κλπ', False),
        ('Ογκολογική Γνωμάτευση', 'Γνωμάτευση από ογκολόγο', True),
        ('Χειρουργικό Πρωτόκολλο', 'Αναφορά χειρουργικής επέμβασης', False),
        ('Σχέδιο Θεραπείας', 'Προτεινόμενο σχέδιο θεραπείας', False),
        ('Επικρίσεις Νοσηλείας', 'Επικρίσεις από νοσηλεία', False),
        
        # Identity & Personal Documents
        ('Αστυνομική Ταυτότητα', 'Ταυτότητα ή αντίγραφο', True),
        ('Διαβατήριο', 'Διαβατήριο ή αντίγραφο', False),
        ('Βεβαίωση ΑΜΚΑ', 'Επίσημη βεβαίωση ΑΜΚΑ', True),
        ('Βεβαίωση ΑΦΜ', 'Βεβαίωση Αριθμού Φορολογικού Μητρώου', False),
        ('Πιστοποιητικό Οικογενειακής Κατάστασης', 'Οικογενειακή κατάσταση από δήμο', True),
        ('Πιστοποιητικό Γέννησης', 'Πιστοποιητικό γέννησης', False),
        
        # Financial & Insurance Documents
        ('Βιβλιάριο Υγείας', 'Βιβλιάριο υγείας ή ασφάλισης', True),
        ('Βεβαίωση Ασφάλισης', 'Βεβαίωση ασφαλιστικής κατάστασης', True),
        ('Πιστοποιητικό Σύνταξης', 'Πιστοποιητικό συνταξιοδότησης', False),
        ('Βεβαίωση Εισοδήματος', 'Βεβαίωση εισοδήματος από εφορία', True),
        ('Φορολογική Ενημερότητα', 'Πιστοποιητικό φορολογικής ενημερότητας', True),
        ('Κάρτα Ανεργίας ΟΑΕΔ', 'Κάρτα ανεργίας από ΟΑΕΔ', False),
        ('Βεβαίωση Επιδομάτων', 'Βεβαίωση λήψης επιδομάτων', False),
        
        # Housing & Utilities
        ('Βεβαίωση Κατοικίας', 'Βεβαίωση διεύθυνσης κατοικίας', True),
        ('Λογαριασμοί Κοινής Ωφέλειας', 'ΔΕΗ, ΕΥΔΑΠ, τηλέφωνο κλπ', True),
        ('Συμβόλαιο Ενοικίασης', 'Συμβόλαιο ενοικίασης κατοικίας', False),
        ('Συμβόλαιο Ιδιοκτησίας', 'Τίτλος ιδιοκτησίας ακινήτου', False),
        
        # Employment Documents
        ('Βεβαίωση Εργοδότη', 'Βεβαίωση από εργοδότη', False),
        ('Σύμβαση Εργασίας', 'Σύμβαση εργασίας', False),
        ('Μισθοδοτικές Καταστάσεις', 'Μισθοδοτικές καταστάσεις', False),
        ('Άδεια Άσκησης Επαγγέλματος', 'Επαγγελματική άδεια', False),
        
        # Legal & Administrative
        ('Παραχώρηση Εξουσιοδότησης', 'Πληρεξούσιο ή εξουσιοδότηση', False),
        ('Έγγραφα Κηδεμονίας', 'Έγγραφα κηδεμονίας ή επιτροπείας', False),
        ('Δικαστική Απόφαση', 'Απόφαση δικαστηρίου', False),
        ('Νομική Εκπροσώπηση', 'Έγγραφα νομικής εκπροσώπησης', False),
        
        # Request-Specific Documents
        ('Αίτηση/Φόρμα', 'Συμπληρωμένη αίτηση ή φόρμα', False),
        ('Δικαιολογητικά Αίτησης', 'Δικαιολογητικά που συνοδεύουν αίτηση', False),
        ('Προηγούμενη Αλληλογραφία', 'Προηγούμενη αλληλογραφία με φορείς', False),
        ('Εξωτερικές Γνωματεύσεις', 'Γνωματεύσεις από εξωτερικούς φορείς', False),
        
        # Educational Documents
        ('Σχολικά Πιστοποιητικά', 'Απολυτήρια, βεβαιώσεις σπουδών', False),
        ('Πτυχίο/Δίπλωμα', 'Πανεπιστημιακά πτυχία και διπλώματα', False),
        ('Πιστοποιητικά Εκπαίδευσης', 'Πιστοποιητικά επαγγελματικής εκπαίδευσης', False),
        
        # Transportation & Mobility
        ('Άδεια Οδήγησης', 'Δίπλωμα οδήγησης', False),
        ('Άδεια Κυκλοφορίας', 'Άδεια κυκλοφορίας οχήματος', False),
        ('Άδεια Στάθμευσης ΑΜΕΑ', 'Ειδική άδεια στάθμευσης', False),
        ('Κάρτα ΜΜΜ', 'Κάρτα μαζικών μέσων μεταφοράς', False),
        
        # Other/Miscellaneous
        ('Φωτογραφία', 'Φωτογραφία ταυτότητας', False),
        ('Συναίνεση/Συγκατάθεση', 'Έγγραφα συναίνεσης', False),
        ('Άλλο Πιστοποιητικό', 'Άλλα πιστοποιητικά', False),
        ('Αλληλογραφία', 'Επιστολές και αλληλογραφία', False),
        ('Σημειώσεις/Παρατηρήσεις', 'Σημειώσεις και παρατηρήσεις', False),
    ]
    
    # Create document types using only existing fields
    for name, description, is_required in document_types:
        DocumentType.objects.get_or_create(
            name=name,
            defaults={
                'description': description,
                'is_required_for_requests': is_required,
            }
        )

def reverse_populate_document_types(apps, schema_editor):
    DocumentType = apps.get_model('records', 'DocumentType')
    # Don't delete existing types on reverse
    pass

class Migration(migrations.Migration):
    
    dependencies = [
        ('records', '0010_remove_request_outcome_alter_action_action_type'),  # Adjust this to your actual previous migration
    ]

    operations = [
        migrations.RunPython(
            populate_document_types,
            reverse_populate_document_types,
        ),
    ]