# records/models/request.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .mixins import TimeStampedModel
from .person import Person
from .org import Center
from .lookups import RequestType, RequestStatus, RequestCategory

User = get_user_model()

class RequestTag(TimeStampedModel):
    """Individual tags that can be combined"""
    name = models.CharField("Όνομα", max_length=100, unique=True)
    category = models.CharField("Κατηγορία", max_length=50, choices=[
        ('kepa', 'ΚΕΠΑ'),
        ('benefits', 'Επιδόματα/Παροχές'),
        ('disability', 'Αναπηρία'),
        ('work', 'Εργασιακά'),
        ('education', 'Εκπαίδευση'),
        ('medical', 'Ιατρικές Υπηρεσίες'),
        ('psychosocial', 'Ψυχοκοινωνική Υποστήριξη'),
        ('transport', 'Μετακίνηση'),
        ('accommodation', 'Φιλοξενία'),
        ('financial', 'Οικονομική Υποστήριξη'),
        ('administrative', 'Διοικητικές Διαδικασίες'),
    ])
    description = models.TextField("Περιγραφή", blank=True)
    is_active = models.BooleanField("Ενεργό", default=True)
    estimated_duration_days = models.PositiveIntegerField("Εκτιμώμενη διάρκεια (ημέρες)", null=True, blank=True)
    
    # Workflow requirements
    requires_documents = models.BooleanField("Απαιτεί έγγραφα", default=False)
    requires_external_contact = models.BooleanField("Απαιτεί επικοινωνία με εξωτερικούς φορείς", default=False)
    
    class Meta:
        ordering = ("category", "name")
        verbose_name = "Ετικέτα Αιτήματος"
        verbose_name_plural = "Ετικέτες Αιτημάτων"
    
    def __str__(self):
        return self.name

class Request(TimeStampedModel):
    """
    Main request/application from beneficiaries for K3 services
    Based on Excel: αρχικά στοιχεία + επόμενα στοιχεία tabs
    """
    
    # Core relationships
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="requests", 
                              verbose_name="Ωφελούμενος")
    center = models.ForeignKey(Center, on_delete=models.PROTECT, null=True, blank=True,
                              verbose_name="Δομή")
    
    # Request classification
    tags = models.ManyToManyField(RequestTag, verbose_name="Ετικέτες", blank=True)
    status = models.ForeignKey(RequestStatus, on_delete=models.PROTECT, 
                              verbose_name="Κατάσταση")
    
    @property
    def get_category_choices(self):
        return RequestTag._meta.get_field('category').choices
    
    primary_category = models.CharField("Κύρια κατηγορία", max_length=50, 
                                      choices=[
                                          ('kepa', 'ΚΕΠΑ'),
                                          ('benefits', 'Επιδόματα/Παροχές'),
                                          ('disability', 'Αναπηρία'),
                                          ('work', 'Εργασιακά'),
                                          ('education', 'Εκπαίδευση'),
                                          ('medical', 'Ιατρικές Υπηρεσίες'),
                                          ('psychosocial', 'Ψυχοκοινωνική Υποστήριξη'),
                                          ('transport', 'Μετακίνηση'),
                                          ('accommodation', 'Φιλοξενία'),
                                          ('financial', 'Οικονομική Υποστήριξη'),
                                          ('administrative', 'Διοικητικές Διαδικασίες'),
                                      ])
    
    category = models.ForeignKey(RequestCategory, on_delete=models.PROTECT, 
                                null=True, blank=True, verbose_name="Κατηγορία")
    # From Excel: Communication details
    COMMUNICATION_METHODS = [
        ('form', 'Φόρμα'),
        ('phone', 'Τηλεφωνική'),
        ('mobile_unit', 'Κινητή Μονάδα'),
    ]
    
    CONTACT_PERSON_TYPES = [
        ('beneficiary', 'Ασθενής'),
        ('caregiver', 'Φροντιστής'),
        ('referral', 'Παραπομπή'),
    ]
      
    PRIORITY_CHOICES = [
        (1, 'Υψηλή'),
        (2, 'Μέτρια'), 
        (3, 'Χαμηλή'),
    ]

    communication_method = models.CharField("Τρόπος επικοινωνίας", max_length=20, 
                                          choices=COMMUNICATION_METHODS, blank=True)
    contact_person_type = models.CharField("Ποιος επικοινώνησε", max_length=20,
                                         choices=CONTACT_PERSON_TYPES, blank=True)
    
    # Dates from Excel structure
    submission_date = models.DateField("Ημερομηνία υποβολής", null=True, blank=True)
    update_date = models.DateField("Ημερομηνία ενημέρωσης", null=True, blank=True)
    due_date = models.DateField("Προθεσμία", null=True, blank=True)
    expiry_date = models.DateField("Ημερ. Λήξης ΓΑΠΑ", blank=True, null=True)
    closed_date = models.DateField("Ημερομηνία κλεισίματος", null=True, blank=True)
    
    # Request details
    subject = models.CharField("Θέμα", max_length=200, blank=True)
        
    # Priority and acceptance
    priority = models.PositiveSmallIntegerField("Προτεραιότητα", 
                                               choices=PRIORITY_CHOICES,
                                               default=2,  # Default to 'Μέτρια'
                                               validators=[MinValueValidator(1), MaxValueValidator(3)])
    is_accepted = models.BooleanField("Δεκτό αίτημα", default=True)
    protocol_number = models.CharField("Αρ. Πρωτοκόλλου", max_length=50, blank=True)
    
    # Assignment and outcome
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="assigned_requests", verbose_name="Ανατέθηκε στον/στην")
    outcome = models.CharField("Έκβαση αιτήματος", max_length=500, blank=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, 
                                  related_name="created_requests", verbose_name="Δημιουργήθηκε από")
    
    # Additional tracking
    number_of_actions = models.PositiveIntegerField("Αριθμός ενεργειών", default=0)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["person", "created_at"]),
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["priority", "created_at"]),
            models.Index(fields=["primary_category"]),
        ]
        verbose_name = "Αίτημα"
        verbose_name_plural = "Αιτήματα"
    
    def __str__(self):
        tags_display = self.get_tags_display() or "Χωρίς ετικέτες"
        return f"{self.person} — {tags_display} ({self.status})"
    
    def get_tags_display(self):
        """Get comma-separated list of tag names"""
        return ", ".join([tag.name for tag in self.tags.all()])
    
    @property
    def estimated_duration(self):
        """Calculate estimated duration based on tags"""
        durations = [tag.estimated_duration_days for tag in self.tags.all() 
                    if tag.estimated_duration_days]
        return max(durations) if durations else None
    
    @property
    def is_overdue(self):
        """Check if request is past due date"""
        if self.due_date and self.status and not self.status.is_closed:
            return timezone.now().date() > self.due_date
        return False
    
    @property
    def days_open(self):
        """Calculate how many days the request has been open"""
        if self.closed_date:
            return (self.closed_date - self.created_at.date()).days
        return (timezone.now().date() - self.created_at.date()).days
    
    @property
    def priority_display(self):
        return dict(self.PRIORITY_CHOICES).get(self.priority, 'Μέτρια')
    
    def save(self, *args, **kwargs):
        # Auto-set primary_category based on most common tag category
        if not self.primary_category and self.pk:
            # Only after the object is saved (so tags can be accessed)
            tags = self.tags.all()
            if tags:
                # Get the most common category among selected tags
                categories = [tag.category for tag in tags]
                if categories:
                    self.primary_category = max(set(categories), key=categories.count)
        
        # Auto-set closed_date when status changes to closed
        if self.status and hasattr(self.status, 'is_closed') and self.status.is_closed and not self.closed_date:
            self.closed_date = timezone.now().date()
        
        # Clear closed_date if status is not closed
        elif self.status and hasattr(self.status, 'is_closed') and not self.status.is_closed:
            self.closed_date = None     
        super().save(*args, **kwargs)
    
    def can_be_edited(self):
        """Check if request can still be edited"""
        return not (self.status and self.status.is_closed)
    
    def get_latest_action(self):
        """Get the most recent action for this request"""
        return self.actions.order_by('-created_at').first()
        
    def get_required_documents(self):
        """Get list of required document types based on selected tags"""
        return [tag for tag in self.tags.all() if tag.requires_documents]
    
    def requires_external_contact(self):
        """Check if any selected tag requires external contact"""
        return self.tags.filter(requires_external_contact=True).exists()


class RequestAttachment(TimeStampedModel):
    """File attachments for requests"""
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField("Αρχείο", upload_to="request_attachments/%Y/%m/")
    original_filename = models.CharField("Όνομα αρχείου", max_length=255)
    file_size = models.PositiveIntegerField("Μέγεθος (bytes)", null=True, blank=True)
    description = models.CharField("Περιγραφή", max_length=200, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Συνημμένο αιτήματος"
        verbose_name_plural = "Συνημμένα αιτημάτων"
    
    def __str__(self):
        return f"{self.original_filename} - {self.request}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.original_filename = self.file.name
            self.file_size = self.file.size
        super().save(*args, **kwargs)



