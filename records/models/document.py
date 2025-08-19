from django.db import models
from django.conf import settings
from .mixins import TimeStampedModel
from .person import Person
from .request import Request

class DocumentType(models.Model):
    """Types of documents for better categorization"""
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
    
    # Document status
    is_verified = models.BooleanField("Επαληθευμένο", default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name="verified_documents",
                                   verbose_name="Επαληθεύτηκε από")
    verified_at = models.DateTimeField("Ημερομηνία επαλήθευσης", null=True, blank=True)
    
    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Έγγραφο"
        verbose_name_plural = "Έγγραφα"
    
    def __str__(self):
        return self.title or self.original_filename or f"Έγγραφο {self.id}"
    
    def save(self, *args, **kwargs):
        if self.file and not self.original_filename:
            self.original_filename = self.file.name
            self.file_size = self.file.size
        super().save(*args, **kwargs)