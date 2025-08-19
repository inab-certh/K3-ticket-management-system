from django.db import models
from django.contrib.auth import get_user_model
from .mixins import TimeStampedModel
from .person import Person
from .request import Request
from .org import ExternalOrganization, Contact
from django.utils import timezone


User = get_user_model()


class Action(TimeStampedModel):
    """
    Actions taken by K3 staff for requests
    Based on Excel: ενέργειες-επαφές tab
    """
    
    # Action type choices - first level
    ACTION_TYPES = [
        ('call', 'Κλήση'),
        ('email', 'Email'),
        ('referral', 'Παραπομπή'),
    ]
    
    # Direction choices - for calls and emails
    DIRECTION_CHOICES = [
        ('from', 'ΑΠΟ'),
        ('to', 'ΠΡΟΣ'),
    ]
    
    # Contact type choices - for calls and emails
    CONTACT_TYPE_CHOICES = [
        ('patient', 'ασθενή'),
        ('caregiver', 'φροντιστή'),
        ('organization', 'φορέα'),
    ]
    
    # Referral type choices
    REFERRAL_CHOICES = [
        ('external_org', 'φορέα'),
        ('internal_dept', 'τμήμα'),
        ('specialist', 'ειδικό'),
    ]
    
    # Core relationships
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="actions", verbose_name="Αίτημα")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="actions",
                              verbose_name="Ωφελούμενος")
    
    # Action details
    action_type = models.CharField("Τύπος ενέργειας", max_length=20, choices=ACTION_TYPES)
    
    # For calls and emails
    direction = models.CharField("Κατεύθυνση", max_length=10, choices=DIRECTION_CHOICES, blank=True, null=True)
    contact_type = models.CharField("Επικοινωνία με", max_length=20, choices=CONTACT_TYPE_CHOICES, blank=True, null=True)
    
    # For referrals
    referral_type = models.CharField("Παραπομπή σε", max_length=20, choices=REFERRAL_CHOICES, blank=True, null=True)
    
    # Rest of the fields
    action_date = models.DateField("Ημερομηνία ενέργειας", default=timezone.now)
    external_org = models.ForeignKey(ExternalOrganization, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Εξωτερικός φορέας")
    contact_person = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Άτομο επικοινωνίας")
    
    # Manual contact info (when external_org/contact_person not in database)
    manual_org_name = models.CharField("Όνομα φορέα (χειροκίνητα)", max_length=200, blank=True)
    manual_contact_name = models.CharField("Όνομα επικοινωνίας (χειροκίνητα)", max_length=200, blank=True)
    manual_contact_position = models.CharField("Θέση (χειροκίνητα)", max_length=100, blank=True)
    manual_contact_phone = models.CharField("Τηλέφωνο (χειροκίνητα)", max_length=20, blank=True)
    manual_contact_email = models.EmailField("Email (χειροκίνητα)", blank=True)
    
    result = models.TextField("Αποτέλεσμα/Απάντηση", blank=True)
    notes = models.TextField("Σημειώσεις", blank=True)
    
    # Follow-up tracking
    requires_follow_up = models.BooleanField("Απαιτεί παρακολούθηση", default=False)
    follow_up_date = models.DateField("Ημερομηνία παρακολούθησης", null=True, blank=True)
    is_completed = models.BooleanField("Ολοκληρώθηκε", default=True)
    
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Εκτελέστηκε από")

    
    class Meta:
        ordering = ["-action_date", "-created_at"]
        indexes = [
            models.Index(fields=["action_date"]),
            models.Index(fields=["request", "action_date"]),
            models.Index(fields=["person", "action_date"]),
            models.Index(fields=["requires_follow_up", "follow_up_date"]),
        ]
        verbose_name = "Ενέργεια"
        verbose_name_plural = "Ενέργειες"
    
    def __str__(self):
        if self.action_type == 'referral':
            referral_display = dict(self.REFERRAL_CHOICES).get(self.referral_type, '')
            return f"Παραπομπή σε {referral_display}"
        else:
            action_display = dict(self.ACTION_TYPES).get(self.action_type, '')
            direction_display = dict(self.DIRECTION_CHOICES).get(self.direction, '')
            contact_display = dict(self.CONTACT_TYPE_CHOICES).get(self.contact_type, '')
            return f"{action_display} {direction_display} {contact_display}"
        
    @property
    def contact_display(self):
        """Get display name for the contact person"""
        if self.contact_person:
            return f"{self.contact_person.name} ({self.contact_person.position})"
        elif self.manual_contact_name:
            pos = f" ({self.manual_contact_position})" if self.manual_contact_position else ""
            return f"{self.manual_contact_name}{pos}"
        return ""
    
    @property
    def organization_display(self):
        """Get display name for the organization"""
        return self.external_org.name if self.external_org else self.manual_org_name
    
    def save(self, *args, **kwargs):
        # Auto-increment action count on the request
        if not self.pk:  # New action
            self.request.number_of_actions += 1
            self.request.save(update_fields=['number_of_actions'])
        
        super().save(*args, **kwargs)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validation rules for action types
        if self.action_type in ['call', 'email']:
            if not self.direction or not self.contact_type:
                raise ValidationError("Για κλήσεις και emails απαιτείται κατεύθυνση και τύπος επικοινωνίας.")
        
        if self.action_type == 'referral':
            if not self.referral_type:
                raise ValidationError("Για παραπομπές απαιτείται ο τύπος παραπομπής.")
        
        # If external_org is selected, contact_person should be from that org
        if self.external_org and self.contact_person:
            if self.contact_person.organization != self.external_org:
                raise ValidationError("Η επαφή πρέπει να ανήκει στον επιλεγμένο φορέα.")
        
        # If follow-up is required, a date should be set
        if self.requires_follow_up and not self.follow_up_date:
            raise ValidationError("Αν απαιτείται παρακολούθηση, πρέπει να οριστεί ημερομηνία.")


class ActionAttachment(TimeStampedModel):
    """File attachments for actions (emails, documents, etc.)"""
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField("Αρχείο", upload_to="action_attachments/%Y/%m/")
    original_filename = models.CharField("Όνομα αρχείου", max_length=255)
    description = models.CharField("Περιγραφή", max_length=200, blank=True)
    
    class Meta:
        verbose_name = "Συνημμένο ενέργειας"
        verbose_name_plural = "Συνημμένα ενεργειών"
    
    def __str__(self):
        return f"{self.original_filename} - {self.action}"