# Updated records/models/document.py

from django.db import models
from django.conf import settings
from .mixins import TimeStampedModel
from .person import Person
from .request import Request

class DocumentType(models.Model):
    name = models.CharField("Όνομα", max_length=100, unique=True)
    description = models.TextField("Περιγραφή", blank=True)
    is_required_for_requests = models.BooleanField("Απαιτείται για αιτήματα", default=False)
    
    class Meta:
        ordering = ("name",)
        verbose_name = "Τύπος εγγράφου"
        verbose_name_plural = "Τύποι εγγράφων"
    
    def __str__(self):
        return self.name


class Document(TimeStampedModel):
    file = models.FileField("Αρχείο", upload_to="documents/%Y/%m/")
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT, 
                                    null=True, blank=True, verbose_name="Τύπος εγγράφου")
    title = models.CharField("Τίτλος", max_length=200, blank=True)
    description = models.TextField("Περιγραφή", blank=True)
    
    # Relationships
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                   null=True, blank=True, verbose_name="Ανέβηκε από")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="documents", 
                              null=True, blank=True, verbose_name="Ωφελούμενος")
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="documents", 
                               null=True, blank=True, verbose_name="Αίτημα")
    
    # File metadata
    file_size = models.PositiveIntegerField("Μέγεθος αρχείου (bytes)", null=True, blank=True)
    original_filename = models.CharField("Αρχικό όνομα αρχείου", max_length=255, blank=True)
    
    # Document validity (for documents that expire)
    issue_date = models.DateField("Ημερομηνία έκδοσης", null=True, blank=True)
    expiry_date = models.DateField("Ημερομηνία λήξης", null=True, blank=True,
                                 help_text="Για έγγραφα που λήγουν (π.χ. ΚΕΠΑ, ταυτότητες)")
    
    # Document status
    is_verified = models.BooleanField("Επαληθευμένο", default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name="verified_documents",
                                   verbose_name="Επαληθεύτηκε από")
    verified_at = models.DateTimeField("Ημερομηνία επαλήθευσης", null=True, blank=True)
    
    # Notes and additional info
    notes = models.TextField("Σημειώσεις", blank=True)
    
    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Έγγραφο"
        verbose_name_plural = "Έγγραφα"
        indexes = [
            models.Index(fields=['person', 'document_type']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return self.title or self.original_filename or f"Έγγραφο {self.id}"
    
    @property
    def is_expired(self):
        """Check if document is expired"""
        if self.expiry_date:
            from django.utils import timezone
            return timezone.now().date() > self.expiry_date
        return False
    
    @property
    def expires_soon(self):
        """Check if document expires within renewal period"""
        if self.expiry_date and self.document_type and self.document_type.renewal_months:
            from django.utils import timezone
            from datetime import timedelta
            warning_date = timezone.now().date() + timedelta(days=self.document_type.renewal_months * 30)
            return self.expiry_date <= warning_date
        return False
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Ensure expiry date is after issue date
        if self.issue_date and self.expiry_date and self.expiry_date <= self.issue_date:
            raise ValidationError("Η ημερομηνία λήξης πρέπει να είναι μετά την ημερομηνία έκδοσης.")
    
    def save(self, *args, **kwargs):
        # Set file metadata if not already set
        if self.file and not self.original_filename:
            self.original_filename = self.file.name
            self.file_size = self.file.size
        
        # Set verification timestamp
        if self.is_verified and not self.verified_at:
            from django.utils import timezone
            self.verified_at = timezone.now()
        
        super().save(*args, **kwargs)