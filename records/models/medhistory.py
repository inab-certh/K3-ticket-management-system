# records/models/medhistory.py
from django.db import models
from django.core.exceptions import ValidationError

from .mixins import TimeStampedModel
from .person import Person
from .lookups import TherapyType            # use the lookup model (do NOT redefine here)
from .icd10 import ICD10Code                # use the shared ICD10 model (do NOT redefine here)


class MedicalHistory(TimeStampedModel):
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name="medical_history")

    disability = models.BooleanField(default=False, verbose_name="Αναπηρία")
    certified_disability = models.BooleanField(default=False, blank=True, verbose_name="Πιστοποιημένη Αναπηρία")
    disability_percentage = models.PositiveIntegerField(blank=True, null=True, verbose_name="Ποσοστό Αναπηρίας")

    kepa_check = models.BooleanField(default=False, verbose_name="Έλεγχος ΚΕΠΑ")
    kepa_expiry = models.DateField(blank=True, null=True, verbose_name="Ημ/νία λήξης ΚΕΠΑ")

    def __str__(self):
        return f"Ιατρικό Ιστορικό: {self.person.first_name} {self.person.last_name}"

    def clean(self):
        # If certified disability is set, a percentage should be provided
        if self.certified_disability and not self.disability_percentage:
            raise ValidationError("Όταν υπάρχει πιστοποιημένη αναπηρία, απαιτείται ποσοστό αναπηρίας.")
        # If no disability at all, clear the percentage
        if not self.disability:
            if self.disability_percentage:
                raise ValidationError("Δεν μπορείτε να δηλώσετε ποσοστό όταν δεν υπάρχει αναπηρία.")
        # If KEPA check is true, an expiry date helps operationally
        if self.kepa_check and not self.kepa_expiry:
            raise ValidationError("Όταν έχει γίνει έλεγχος ΚΕΠΑ, ορίστε και ημερομηνία λήξης.")
    
    class Meta:
        verbose_name = "Ιατρικό Ιστορικό"
        verbose_name_plural = "Ιατρικά Ιστορικά"


class Neoplasm(TimeStampedModel):
    
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="neoplasms",
        verbose_name="Ωφελούμενος/η",
    )
        
    # Add cascading fields
    icd10_category = models.ForeignKey(
        'ICD10Category', 
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Κατηγορία νεοπλάσματος"
    )
    icd10_subcategory = models.ForeignKey(
        'ICD10Subcategory',
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name="Υποκατηγορία"
    )
    
    # Keep your existing fields
    
    icd10_code = models.ForeignKey(
        ICD10Code,
        on_delete=models.PROTECT,
        verbose_name="Είδος",
    )
    localization = models.CharField(max_length=255, blank=True, null=True, verbose_name="Εντοπισμός")

    metastasis = models.BooleanField(default=False, verbose_name="Μεταστάσεις")
    surgery = models.BooleanField(default=False, verbose_name="Χειρουργική επέμβαση")
    surgery_hospital = models.CharField(max_length=255, blank=True, null=True, verbose_name="Νοσοκομείο Χειρουργείου")
    scheduled_treatment = models.TextField(blank=True, null=True, verbose_name="Προγραμματισμένη θεραπεία")

    def __str__(self):
        category_name = self.icd10_category.name if self.icd10_category else "Κατηγορία"
        code_info = f" - {self.icd10_code.code}" if self.icd10_code else ""
        loc = f" ({self.localization})" if self.localization else ""
        return f"{category_name}{code_info}{loc}".strip()

    def clean(self):
        # Max 4 neoplasms per person & category
        if self.person and self.icd10_category:
            existing = (
                Neoplasm.objects
                .filter(person=self.person, icd10_category=self.icd10_category)
                .exclude(id=self.id)
                .count()
            )
            if existing >= 4:
                raise ValidationError("Ένα άτομο μπορεί να έχει μέχρι 4 νεοπλάσματα ανά κατηγορία.")
        # If surgery was done, hospital is required
        if self.surgery and not self.surgery_hospital:
            raise ValidationError("Αν έχει γίνει χειρουργείο, πρέπει να δηλωθεί το νοσοκομείο.")

    class Meta:
        verbose_name = "Νεόπλασμα"
        verbose_name_plural = "Νεοπλάσματα"
        unique_together = ("person", "icd10_category", "icd10_code")


class Therapy(TimeStampedModel):
    THERAPY_TYPES = [
        ("chemotherapy", "Χημειοθεραπεία"),
        ("radiotherapy", "Ακτινοθεραπεία"), 
        ("hormone_therapy", "Ορμονοθεραπεία"),
        ("targeted_therapy", "Στοχευμένη θεραπεία"),
        ("immunotherapy", "Ανοσοθεραπεία"),
        ("gene_therapy", "Γονιδιακή"),
        ("alternative", "Εναλλακτική"),
        ("stem_cell", "Βλαστοκύτταρα"),
        ("other", "Άλλη θεραπεία"),
    ]
    
    neoplasm = models.ForeignKey(Neoplasm, on_delete=models.CASCADE, related_name="therapies", null=True, blank=True)
    #therapy_type = models.ForeignKey(TherapyType, on_delete=models.PROTECT, verbose_name="Θεραπεία")
    therapy_type = models.CharField(
        "Είδος θεραπείας",
        max_length=20,
        choices=THERAPY_TYPES
    )
    hospital_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Νοσοκομείο")
    start_date = models.DateField(blank=True, null=True, verbose_name="Ημερομηνία Έναρξης")
    notes = models.TextField(blank=True, null=True, verbose_name="Σχόλια")

    class Meta:
        verbose_name = "Θεραπεία"
        verbose_name_plural = "Θεραπείες"
        
        
    def __str__(self):
        therapy_name = self.get_therapy_type_display()
        date_info = f" ({self.start_date})" if self.start_date else ""
        return f"{therapy_name}{date_info}"
        
        

class Comorbidity(TimeStampedModel):
    """Συνοδά νοσήματα - References Person's BMI instead of duplicating"""
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name="comorbidity")

    # Conditions from your Excel data
    arterial_disease = models.BooleanField("Αρτηριακές παθήσεις", default=False)
    cardiovascular_disease = models.BooleanField("Καρδιαγγειακά νοσήματα", default=False)
    copd = models.BooleanField("ΧΑΠ", default=False)
    diabetes = models.BooleanField("Σακχαρώδης διαβήτης", default=False)
    psychiatric_disorder = models.BooleanField("Ψυχιατρικά νοσήματα", default=False)
    mobility_issues = models.BooleanField("Κινητικά προβλήματα", default=False)
    nephropathy = models.BooleanField("Νεφροπάθεια", default=False)

    other_conditions = models.TextField("Άλλες παθήσεις", blank=True, null=True)
    #notes = models.TextField("Παρατηρήσεις", blank=True, null=True)

    # Reference Person's weight/height instead of duplicating
    @property
    def weight(self):
        return self.person.weight

    @property  
    def height(self):
        return self.person.height

    @property
    def bmi(self):
        return self.person.bmi

    @property
    def bmi_category(self):
        return self.person.bmi_category

    def __str__(self):
        return f"Συννοσηρότητες: {self.person.first_name} {self.person.last_name}"

    class Meta:
        verbose_name = "Συννοσηρότητα"
        verbose_name_plural = "Συννοσηρότητες"
