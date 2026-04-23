from django.db import models
from .mixins import TimeStampedModel
from .lookups import Municipality


class Center(TimeStampedModel):
    """Organization/Structure handling a request - K3 Centers"""
    name = models.CharField("Όνομα", max_length=160, unique=True)
    code = models.CharField("Κωδικός", max_length=20, blank=True, unique=True)
    address = models.CharField("Διεύθυνση", max_length=240, blank=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL, 
                                   null=True, blank=True, verbose_name="Δήμος")
    phone = models.CharField("Τηλέφωνο", max_length=40, blank=True)
    email = models.EmailField("Email", blank=True)
    is_active = models.BooleanField("Ενεργό", default=True)
    
    class Meta:
        ordering = ("name",)
        verbose_name = "Κέντρο"
        verbose_name_plural = "Κέντρα"
    
    def __str__(self):
        return self.name


class ExternalOrganization(TimeStampedModel):
    """External organizations that K3 staff contact (from actions)"""
    name = models.CharField("Όνομα φορέα", max_length=200)
    org_type = models.CharField("Τύπος", max_length=100, choices=[
        ('hospital', 'Νοσοκομείο'),
        ('municipality', 'Δήμος'),
        ('social_service', 'Κοινωνική Υπηρεσία'),
        ('insurance', 'Ασφαλιστικός Φορέας'),
        ('ministry', 'Υπουργείο'),
        ('kep', 'ΚΕΠ'),
        ('other', 'Άλλο'),
    ], blank=True)
    
    # Contact details
    address = models.CharField("Διεύθυνση", max_length=240, blank=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL, 
                                   null=True, blank=True, verbose_name="Δήμος")
    phone = models.CharField("Τηλέφωνο", max_length=40, blank=True)
    email = models.EmailField("Email", blank=True)
    website = models.URLField("Ιστοσελίδα", blank=True)
    
    # Operational info
    is_active = models.BooleanField("Ενεργός", default=True)
    notes = models.TextField("Σημειώσεις", blank=True)
    
    class Meta:
        ordering = ("org_type", "name")
        verbose_name = "Εξωτερικός Φορέας"
        verbose_name_plural = "Εξωτερικοί Φορείς"
    
    def __str__(self):
        return self.name


class Contact(TimeStampedModel):
    """Contact persons within external organizations"""
    organization = models.ForeignKey(ExternalOrganization, on_delete=models.CASCADE, 
                                   related_name="contacts", verbose_name="Φορέας")
    name = models.CharField("Όνομα", max_length=100)
    position = models.CharField("Θέση", max_length=100, blank=True)
    department = models.CharField("Τμήμα", max_length=100, blank=True)
    
    # Contact details
    phone = models.CharField("Τηλέφωνο", max_length=40, blank=True)
    mobile = models.CharField("Κινητό", max_length=40, blank=True)
    email = models.EmailField("Email", blank=True)
    
    is_primary = models.BooleanField("Κύρια επαφή", default=False)
    notes = models.TextField("Σημειώσεις", blank=True)
    
    class Meta:
        ordering = ("-is_primary", "name")
        verbose_name = "Επαφή"
        verbose_name_plural = "Επαφές"
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"