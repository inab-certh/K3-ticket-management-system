from django.db import models
#from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from .validators import validate_vat, validate_amka, validate_id_card
from django.core.exceptions import ValidationError
import re
from .org import Center  # or wherever your Center model is



#from records.utils import greek_upper_no_tone
from .mixins import TimeStampedModel
from .geography import *
from .lookups import InsuranceProvider, EmploymentStatus
from datetime import date

class Gender(models.TextChoices):
    MALE = "male", "Άνδρας"
    FEMALE = "female", "Γυναίκα"
    OTHER = "other", "Άλλο"
    
class MaritalStatus(models.TextChoices):
    SINGLE = "single", "Άγαμος/η"
    MARRIED = "married", "Έγγαμος/η"
    COHABITING = "cohabiting", "Σε συμβίωση"
    DIVORCED = "divorced", "Διαζευγμένος/η"
    WIDOWED = "widowed", "Χήρος/α"
        

class Person(TimeStampedModel):
    last_name = models.CharField("Επώνυμο", max_length=60)
    first_name = models.CharField("Όνομα", max_length=60)
    father_name = models.CharField("Πατρώνυμο", max_length=60, blank=True, null=True)
    mother_name = models.CharField("Μητρώνυμο", max_length=60, blank=True, null=True)
    
    #birth_date = models.DateField("Ημερομηνία γέννησης", null=True, blank=True)
    birth_year = models.IntegerField("Έτος γέννησης", null=True, blank=True)  # From your Excel
    #age = models.IntegerField("Ηλικία", blank=True, null=True)  # Can be calculated
    gender = models.CharField("Φύλο", max_length=8, choices=Gender.choices, blank=True)
    
    marital_status = models.CharField("Οικογενειακή κατάσταση", max_length=15, 
                                    choices=MaritalStatus.choices, blank=True)
    children_count = models.IntegerField("Αριθμός τέκνων", default=0,
                                       validators=[MinValueValidator(0)])
    minors = models.IntegerField("Ανήλικα", default=0, validators=[MinValueValidator(0)])
    students = models.IntegerField("Φοιτητές", default=0, validators=[MinValueValidator(0)])
    no_military_service = models.IntegerField("Όχι θητεία", default=0, validators=[MinValueValidator(0)])
       
    nationality = models.CharField("Υπηκοότητα", max_length=100, blank=True, default="Ελληνική")
    citizenship = models.CharField("Ιθαγένεια", max_length=100, blank=True, default="Ελληνική")
    
    vat = models.CharField("ΑΦΜ", max_length=9, unique=True, blank=True, null=True, 
                          validators=[validate_vat])
    amka = models.CharField("ΑΜΚΑ", max_length=11, unique=True, blank=True, null=True,
                           validators=[validate_amka], db_index=True)
    id_card = models.CharField("Α.Δ.Τ.", max_length=8, unique=True, blank=True, null=True,
                              validators=[validate_id_card])
    
    # Contact Information
    phone_validator = RegexValidator(r"^\+?[0-9]{7,15}$", "Δώστε έγκυρο τηλέφωνο")
    landline = models.CharField("Σταθερό τηλ.", max_length=15, blank=True, validators=[phone_validator])
    mobile = models.CharField("Κινητό τηλ.", max_length=15, blank=True, validators=[phone_validator])
    email = models.EmailField("Email", blank=True)
    
    # Address
    address = models.CharField("Διεύθυνση", max_length=200, blank=True)
    city = models.CharField("Πόλη/Χωριό/Περιοχή", max_length=100, blank=True)  # From Excel
    postal_code = models.CharField("Τ.Κ.", max_length=10, blank=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL, 
                               null=True, blank=True, verbose_name="Δήμος")
    regional_unit = models.ForeignKey(RegionalUnit, on_delete=models.SET_NULL, 
                                     null=True, blank=True, verbose_name="Περιφεριακή Ενότητα")                        
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Περιφέρεια")  # From Excel
    
    # Physical characteristics (from Excel)
    weight = models.FloatField("Βάρος (kg)", null=True, blank=True,
                              validators=[MinValueValidator(20), MaxValueValidator(300)])
    height = models.FloatField("Ύψος (m)", null=True, blank=True,
                              validators=[MinValueValidator(0.5), MaxValueValidator(2.5)])
    
    # Administrative (from Excel structure)
    #STRUCTURE_CHOICES = [        ('ΑΘΗΝΑ', 'ΑΘΗΝΑ'),        ('ΑΛΕΞΑΝΔΡΟΥΠΟΛΗ', 'ΑΛΕΞΑΝΔΡΟΥΠΟΛΗ'),        ('ΘΕΣΣΑΛΟΝΙΚΗ', 'ΘΕΣΣΑΛΟΝΙΚΗ'),    ]

    #structure = models.CharField("Δομή", max_length=50, blank=True)
    center = models.ForeignKey(
        Center, 
        on_delete=models.CASCADE, 
        verbose_name="Δομή/Κέντρο",
        related_name='people',
        null=True, 
        blank=True
    )
    registration_number = models.IntegerField("Αριθμός εγγραφής", unique=True, null=True, blank=True)
    KNOWLEDGE_SOURCE = [
        ('other_patient', 'Άλλον ασθενή'),
        ('other_org', 'Άλλον οργανισμό'),
        ('known', 'Γνωστό'),
        ('print', 'Έντυπο'),
        ('internet', 'Διαδίκτυο'),
        ('pgna', 'ΠΓΝΑ'),
        ('anh', 'ΑΝΘ'),
        ('other', 'Άλλη πηγή'),
    ]
    
    knowledge_source = models.CharField("Γνώση της Κ3 από", max_length=20,
                                      choices=KNOWLEDGE_SOURCE, blank=True)
    
    class InsuranceStatus(models.TextChoices):
        INSURED = "insured", "Ασφαλισμένος/η"
        UNINSURED = "uninsured", "Ανασφάλιστος/η"
        INDIRECT = "indirectlyinsured", "Έμμεσα Ασφαλισμένος/η"

    insurance_status = models.CharField("Ασφάλιση", max_length=20, choices=InsuranceStatus.choices)
    
    class InsuranceProvider(models.TextChoices):
        IKA = "ika", "ΙΚΑ"
        OGA = "oga", "ΟΓΑ"
        ETAA = "etaa", "ΕΤΑΑ"
        SPECIAL_FUNDS = "special_funds", "Ειδικά Ταμεία"
        OAEE = "oaee", "ΟΑΕΕ"
        NAT = "nat", "ΝΑΤ"
        PUBLIC = "public", "ΔΗΜΟΣΙΟ"
        TSMEDE = "tsmede", "ΤΣΜΕΔΕ"
        NONE = "none", "Δεν Έχω"
        
    insurance_provider = models.CharField(
        "Φορέας κύριας ασφάλισης",
        max_length=20,
        choices=InsuranceProvider.choices,
        blank=True
    )
    special_funds = models.CharField("Ειδικά ταμεία", max_length=255, blank=True)

    # Pensions (from Excel)
    widow_pension = models.BooleanField("Συντάξη χηρείας", default=False)
    disability_pension = models.BooleanField("Σύνταξη αναπηρίας", default=False)
    
    class EmploymentStatusChoices(models.TextChoices):
        UNEMPLOYED = "unemployed", "Άνεργος/η"
        EMPLOYED = "employed", "Εργαζόμενος/η"
        RETIRED = "retired", "Συνταξιούχος"
        HOUSEWORK = "housework", "Οικιακά"
        STUDENT = "student", "Φοιτητής"
        RETIRED_AND_EMPLOYED = "retired_employed", "Συντ & Εργαζ."
        OTHER = "other", "Άλλο"
        
    # Employment Status
    status = models.CharField(
        "Εργασιακή κατάσταση",
        max_length=20,
        choices=EmploymentStatusChoices.choices,
        blank=True
    )
    
    # Unemployment info
    unemployment_card = models.BooleanField("Κάρτα ανεργίας", default=False)
    unemployment_registration_date = models.DateField("Ημερομηνία εγγραφής ΟΑΕΔ", blank=True, null=True)

    # Job details
    profession = models.CharField("Επάγγελμα", max_length=255, blank=True)
    specialization = models.CharField("Ειδικότητα", max_length=255, blank=True)

    class EmploymentType(models.TextChoices):
        EMPLOYEE = "employee", "Υπάλληλος"
        FREELANCER = "freelancer", "Ελεύθερος Επαγγελματίας"
        OWNER = "owner", "Ιδιοκτήτης"

    employment_type = models.CharField("Εργασιακή σχέση", max_length=15,
                                     choices=EmploymentType.choices, blank=True)
    
    # Employer info
    employer_name = models.CharField("Εργοδότης", max_length=200, blank=True)
    employer_legal_form = models.CharField("Νομική μορφή εργοδότη", max_length=100, blank=True)
    hire_date = models.DateField("Ημερομηνία πρόσληψης", blank=True, null=True)

    class WorkSchedule(models.TextChoices):
        FULL_TIME = "full_time", "Πλήρης"
        PART_TIME = "part_time", "Μερική"
        HOURLY = "hourly", "Ωρομίσθια"
        SEASONAL = "seasonal", "Εποχική"

    work_schedule = models.CharField("Μορφή απασχόλησης", max_length=15,
                                   choices=WorkSchedule.choices, blank=True)
    
    class ContractType(models.TextChoices):
        INDEFINITE = "indefinite", "Αορίστου χρόνου"
        FIXED_TERM = "fixed_term", "Ορισμένου χρόνου"
        PROJECT = "project", "Έργου"
        OTHER = "other", "Άλλο"

    contract_type = models.CharField("Είδος σύμβασης", max_length=15,
                                   choices=ContractType.choices, blank=True)
    
    def clean(self):
        super().clean()
        if self.children_count == 0:
            if self.minors > 0 or self.students > 0 or self.no_military_service > 0:
                raise ValidationError("Δεν μπορείτε να έχετε ανήλικα/φοιτητές/άτομα χωρίς θητεία αν δεν έχετε τέκνα")
        
        # Each category can't exceed total children individually
        if self.minors > self.children_count:
            raise ValidationError("Τα ανήλικα δεν μπορούν να υπερβαίνουν τον αριθμό τέκνων")
        if self.students > self.children_count:
            raise ValidationError("Οι φοιτητές δεν μπορούν να υπερβαίνουν τον αριθμό τέκνων")
        if self.no_military_service > self.children_count:
            raise ValidationError("Όσοι δεν έχουν κάνει θητεία δεν μπορούν να υπερβαίνουν τον αριθμό τέκνων")
            
        if self.mobile:
            mobile_clean = re.sub(r'[^\d]', '', str(self.mobile))  # Remove non-digits
            if not re.match(r'^69\d{8}$', mobile_clean):
                raise ValidationError("Το κινητό πρέπει να είναι της μορφής 69XXXXXXXX")
        
        # Landline validation (Greek format: 2XXXXXXXXX)
        if self.landline:
            landline_clean = re.sub(r'[^\d]', '', str(self.landline))
            if not re.match(r'^2\d{9}$', landline_clean):
                raise ValidationError("Το σταθερό τηλέφωνο πρέπει να είναι της μορφής 2XXXXXXXXX")
        
        # Postal code validation (Greek: 5 digits)
        if self.postal_code:
            if not re.match(r'^\d{5}$', str(self.postal_code)):
                raise ValidationError("Ο ταχυδρομικός κώδικας πρέπει να έχει 5 ψηφία χωρίς κενά")    
    
    
    @property
    def bmi(self):
        """Calculate BMI if weight and height available"""
        if self.weight and self.height:
            return round(self.weight / (self.height ** 2), 1)
        return None
    
    @property
    def bmi_category(self):
        bmi = self.bmi
        if not bmi:
            return None
        if bmi < 18.5:
            return 'Λιποβαρής'
        elif bmi < 25:
            return 'Φυσιολογικό βάρος'  
        elif bmi < 30:
            return 'Υπέρβαρος'
        elif bmi < 35:
            return 'Παχύσαρκος Ι'
        elif bmi < 40:
            return 'Παχύσαρκος ΙΙ'
        else:
            return 'Παχύσαρκος ΙΙΙ'
    
    @property
    def calculated_age(self):
        """Calculate age from birth_date or birth_year"""
        if self.birth_year:
            return date.today().year - self.birth_year
        return None

    def save(self, *args, **kwargs):
        if not self.registration_number:
            # Get the highest existing registration number
            last_person = Person.objects.aggregate(
                max_reg=models.Max('registration_number')
            )['max_reg']
            self.registration_number = (last_person or 0) + 1
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ("last_name", "first_name")
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["amka"]),
            models.Index(fields=["vat"]),
        ]
        verbose_name = "Ωφελούμενος"
        verbose_name_plural = "Ωφελούμενοι"

    def __str__(self):
        return f"{self.last_name} {self.first_name}".strip()


class ContactRelation(models.TextChoices):
    PARENT = "parent", "Γονέας"
    GUARDIAN = "guardian", "Κηδεμόνας"
    SIBLING = "sibling", "Αδερφός/ή"
    FRIEND = "friend", "Φίλος/η"
    SPOUSE = "spouse", "Σύζυγος"
    CHILD = "child", "Γιος/Κόρη"
    RELATIVE = "relative", "Συγγενής"
    CAREGIVER = "caregiver", "Φροντιστής"
    OTHER = "other", "Άλλο"


class ContactPerson(TimeStampedModel):
    """Στοιχεία 3ου ατόμου για επικοινωνία"""
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="contacts")

    last_name = models.CharField("Επώνυμο", max_length=60, blank=True)
    first_name = models.CharField("Όνομα", max_length=60, blank=True)
    relation = models.CharField("Σχέση", max_length=15, choices=ContactRelation.choices, blank=True)

    # Contact info
    phone_validator = RegexValidator(r"^\+?[0-9]{7,15}$", "Δώστε έγκυρο τηλέφωνο")
    landline = models.CharField("Σταθερό", max_length=15, blank=True, validators=[phone_validator])
    mobile = models.CharField("Κινητό", max_length=15, blank=True, validators=[phone_validator])
    email = models.EmailField("Email", blank=True)
    
    # Address
    address = models.CharField("Διεύθυνση", max_length=200, blank=True)
    city = models.CharField("Πόλη", max_length=100, blank=True)
    postal_code = models.CharField("Τ.Κ.", max_length=10, blank=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL, 
                                   null=True, blank=True, verbose_name="Δήμος")

    # Priority contact
    is_primary = models.BooleanField("Κύρια επαφή", default=False)
    notes = models.TextField("Σημειώσεις", blank=True)

    class Meta:
        ordering = ("-is_primary", "last_name", "first_name")
        verbose_name = "Άτομο επικοινωνίας"
        verbose_name_plural = "Άτομα επικοινωνίας"

    def __str__(self):
        name = f"{self.last_name} {self.first_name}".strip()
        relation = dict(ContactRelation.choices).get(self.relation, "")
        return f"{name} ({relation})" if relation else name

    def save(self, *args, **kwargs):
        # Ensure only one primary contact per person
        if self.is_primary:
            ContactPerson.objects.filter(person=self.person, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)