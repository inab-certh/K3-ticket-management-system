from django.db import models

from .geography import Municipality

class NamedLookup(models.Model):
    """Base class for all lookup tables"""
    name = models.CharField("Όνομα", max_length=200, unique=True)
    name_en = models.CharField("English Name", max_length=200, blank=True)  # For international use
    code = models.CharField("Κωδικός", max_length=40, blank=True, unique=True)
    is_active = models.BooleanField("Ενεργό", default=True)
    sort_order = models.IntegerField("Σειρά", default=0)  # For custom ordering
    #notes = models.TextField("Σημειώσεις", blank=True)
    
    class Meta:
        abstract = True
        ordering = ("sort_order", "name")
    
    def __str__(self):
        return self.name

# Request System Lookups
class RequestCategory(NamedLookup):
    """Κατηγορίες αιτημάτων - Top level grouping"""
    description = models.TextField("Περιγραφή", blank=True)
    
    class Meta:
        verbose_name = "Κατηγορία αιτήματος"
        verbose_name_plural = "Κατηγορίες αιτημάτων"


class RequestType(NamedLookup):
    """Τύποι αιτημάτων - Based on your Excel data"""
    category = models.ForeignKey(RequestCategory, on_delete=models.PROTECT,
                                related_name="request_types", null=True, blank=True,
                                verbose_name="Κατηγορία")
    description = models.TextField("Περιγραφή", blank=True)
    requires_documents = models.BooleanField("Απαιτεί έγγραφα", default=False)
    estimated_duration_days = models.IntegerField("Εκτιμώμενη διάρκεια (ημέρες)", null=True, blank=True)
    is_urgent = models.BooleanField("Επείγον", default=False)
    priority_level = models.IntegerField("Προτεραιότητα", default=5, help_text="1=Υψηλή, 5=Κανονική")
    
    class Meta:
        verbose_name = "Τύπος αιτήματος"
        verbose_name_plural = "Τύποι αιτημάτων"
        ordering = ("category__name", "name")

    # Pre-populate based on your Excel data:
    # - Δημιουργία φακέλου ΚΕΠΑ
    # - Απαλλαγές-Παροχές  
    # - Εύρεση Νοσοκομείου
    # - Θέση ΑΜΕΑ
    # - Ενημέρωση για Επιδόματα
    # - Εξοδα Μετακίνησης
    # - Δωρεάν Φιλοξενία για Θεραπείες


class RequestStatus(NamedLookup):
    """Καταστάσεις αιτημάτων - From your Excel"""
    is_closed = models.BooleanField("Κλειστό", default=False)
    is_pending = models.BooleanField("Εκκρεμεί", default=False)
    requires_action = models.BooleanField("Απαιτεί ενέργεια", default=True)
    color_code = models.CharField("Χρώμα", max_length=7, blank=True, 
                                 help_text="Hex color for UI display")
    
    class Meta:
        verbose_name = "Κατηγορία αιτήματος"
        verbose_name_plural = "Κατηγορίες αιτημάτων"

    # Based on your Excel:
    # - Εκκρεμεί, κοινοποίηση αποτελέσματος
    # - Ολοκλήρωση  
    # - Αξιολόγηση
    # - Εκκρεμεί, απάντηση ωφελούμενου
    # - Σε εξέλιξη


# Action/Communication Lookups
class ActionType(NamedLookup):
    """Τύποι ενεργειών - From your Excel actions"""
    is_communication = models.BooleanField("Είναι επικοινωνία", default=True)
    requires_contact_details = models.BooleanField("Απαιτεί στοιχεία επικοινωνίας", default=True)
    default_duration_minutes = models.IntegerField("Προεπιλεγμένη διάρκεια (λεπτά)", null=True, blank=True)
    
    class Meta:
        verbose_name = "Τύπος ενέργειας"
        verbose_name_plural = "Τύποι ενεργειών"

    # Based on your Excel:
    # - Κλήση ΠΡΟΣ
    # - Κλήση ΑΠΟ  
    # - Email ΠΡΟΣ
    # - Email ΑΠΟ
    # - Επίσκεψη ΠΡΟΣ
    # - Επίσκεψη ΑΠΟ


class CommunicationChannel(NamedLookup):
    """Κανάλια επικοινωνίας"""
    supports_attachments = models.BooleanField("Υποστηρίζει συνημμένα", default=False)
    is_synchronous = models.BooleanField("Σύγχρονη επικοινωνία", default=True)
    
    class Meta:
        verbose_name = "Κανάλι επικοινωνίας"
        verbose_name_plural = "Κανάλια επικοινωνίας"


# Medical/Insurance Lookups
class InsuranceProvider(NamedLookup):
    """Ασφαλιστικοί φορείς"""
    provider_type = models.CharField("Τύπος φορέα", max_length=50, choices=[
        ('public', 'Δημόσιος'),
        ('private', 'Ιδιωτικός'),
        ('special', 'Ειδικό ταμείο'),
    ], blank=True)
    contact_phone = models.CharField("Τηλέφωνο", max_length=20, blank=True)
    contact_email = models.EmailField("Email", blank=True)
    website = models.URLField("Ιστοσελίδα", blank=True)
    
    class Meta:
        verbose_name = "Ασφαλιστικός φορέας"
        verbose_name_plural = "Ασφαλιστικοί φορείς"

    # Pre-populate: ΔΗΜΟΣΙΟ, ΕΟΠΥΥ, ΙΚΑ, ΟΓΑ, Τεχνητό Επιμελητήριο, etc.


class EmploymentStatus(NamedLookup):
    """Εργασιακές καταστάσεις"""
    affects_insurance = models.BooleanField("Επηρεάζει ασφάλιση", default=False)
    is_unemployed = models.BooleanField("Άνεργος", default=False)
    is_retired = models.BooleanField("Συνταξιούχος", default=False)
    
    class Meta:
        verbose_name = "Εργασιακή κατάσταση"
        verbose_name_plural = "Εργασιακές καταστάσεις"


class TherapyType(NamedLookup):
    """Τύποι θεραπειών - From your Excel"""
    therapy_category = models.CharField("Κατηγορία", max_length=50, choices=[
        ('systemic', 'Συστηματική'),
        ('local', 'Τοπική'),  
        ('surgical', 'Χειρουργική'),
        ('supportive', 'Υποστηρικτική'),
        ('palliative', 'Παρηγορητική'),
    ], blank=True)
    requires_hospitalization = models.BooleanField("Απαιτεί νοσηλεία", default=False)
    typical_duration_weeks = models.IntegerField("Τυπική διάρκεια (εβδομάδες)", null=True, blank=True)
    
    class Meta:
        verbose_name = "Τύπος θεραπείας"
        verbose_name_plural = "Τύποι θεραπειών"

    # From your Excel: Χημειοθεραπεία, Ακτινοθεραπεία, Ορμονοθεραπεία


class Hospital(NamedLookup):
    """Νοσοκομεία"""
    hospital_type = models.CharField("Τύπος νοσοκομείου", max_length=50, choices=[
        ('public', 'Δημόσιο'),
        ('private', 'Ιδιωτικό'),
        ('university', 'Πανεπιστημιακό'),
    ], blank=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL, 
                                   null=True, blank=True, verbose_name="Δήμος")
    address = models.CharField("Διεύθυνση", max_length=200, blank=True)
    phone = models.CharField("Τηλέφωνο", max_length=20, blank=True)
    website = models.URLField("Ιστοσελίδα", blank=True)
    
    # Specialties
    has_oncology = models.BooleanField("Ογκολογική", default=False)
    has_radiotherapy = models.BooleanField("Ακτινοθεραπεία", default=False)
    has_chemotherapy = models.BooleanField("Χημειοθεραπεία", default=False)
    has_surgery = models.BooleanField("Χειρουργική", default=False)
    
    class Meta:
        verbose_name = "Νοσοκομείο"
        verbose_name_plural = "Νοσοκομεία"
        ordering = ("name",)

    # From your Excel: Αγίων Αναργύρων, Άγιος Σάββας, Υγεία, Αλεξάνδρα, 
    # Έλενα, Ερρίκος Ντυνάν, Ιατρόπολις


# Organization Types (for actions/contacts)
class OrganizationType(NamedLookup):
    """Τύποι οργανισμών"""
    can_be_contacted = models.BooleanField("Μπορεί να επικοινωνήσει", default=True)
    is_government = models.BooleanField("Κρατικός οργανισμός", default=False)
    
    class Meta:
        verbose_name = "Τύπος οργανισμού"
        verbose_name_plural = "Τύποι οργανισμών"


class Organization(NamedLookup):
    """Οργανισμοί/Φορείς που εμφανίζονται στις ενέργειες"""
    organization_type = models.ForeignKey(OrganizationType, on_delete=models.SET_NULL,
                                        null=True, blank=True, verbose_name="Τύπος")
    municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL,
                                   null=True, blank=True, verbose_name="Δήμος")
    address = models.CharField("Διεύθυνση", max_length=200, blank=True)
    phone = models.CharField("Τηλέφωνο", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)
    website = models.URLField("Ιστοσελίδα", blank=True)
    
    class Meta:
        verbose_name = "Οργανισμός"
        verbose_name_plural = "Οργανισμοί"
        ordering = ("organization_type__name", "name")

    # From your Excel actions:
    # - Τμήμα Εσόδων Δ.ΠΕΤΡΟΎΠΟΛΗΣ
    # - Κοινωνική Υπηρεσία Δ.Πετρούπολης  
    # - Κοινωνική Υπηρεσία Αγ.Δημητρίου
    # - Νοσοκομείο Άγιος Σάββας


# Comorbidities
class ComorbidityType(NamedLookup):
    """Τύποι συνοδών νοσημάτων"""
    affects_treatment = models.BooleanField("Επηρεάζει θεραπεία", default=False)
    requires_monitoring = models.BooleanField("Απαιτεί παρακολούθηση", default=False)
    
    class Meta:
        verbose_name = "Τύπος συνοδού νοσήματος"
        verbose_name_plural = "Τύποι συνοδών νοσημάτων"

    # From your Excel: Αρτηριακές παθήσεις, Καρδιαγγειακά νοσήματα, ΧΑΠ,
    # Σακχαρώδης διαβήτης, Ψυχιατρικά νοσήματα, Κινητικά προβλήματα, 
    # Νεφροπάθεια, Ρευματοειδής Αρθρίτιδα