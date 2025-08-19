from django.db import models

class ICD10Category(models.Model):
    """Main ICD-10 categories"""
    code_range = models.CharField("Κωδικοί", max_length=20, unique=True)  # e.g., "C00-C97"
    name = models.CharField("Όνομα", max_length=200)
    name_en = models.CharField("English Name", max_length=200, blank=True)
    description = models.TextField("Περιγραφή", blank=True)
    is_cancer_related = models.BooleanField("Σχετίζεται με καρκίνο", default=True)
    sort_order = models.PositiveIntegerField("Σειρά", default=0)
    
    class Meta:
        ordering = ("sort_order", "code_range")
        verbose_name = "ICD-10 Κατηγορία"
        verbose_name_plural = "ICD-10 Κατηγορίες"
    
    def __str__(self):
        return f"{self.code_range} - {self.name}"


class ICD10Subcategory(models.Model):
    """Subcategories within main categories (e.g., Αίμα-Λεμφικό, Αναπνευστικό)"""
    category = models.ForeignKey(ICD10Category, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField("Όνομα", max_length=200)
    description = models.TextField("Περιγραφή", blank=True)
    code_range_start = models.CharField("Αρχή κωδικών", max_length=10, blank=True)
    code_range_end = models.CharField("Τέλος κωδικών", max_length=10, blank=True)
    sort_order = models.PositiveIntegerField("Σειρά", default=0)
    
    class Meta:
        ordering = ("category", "sort_order", "name")
        verbose_name = "ICD-10 Υποκατηγορία"
        verbose_name_plural = "ICD-10 Υποκατηγορίες"
    
    def __str__(self):
        return f"{self.name} ({self.category.code_range})"


class ICD10Code(models.Model):
    """Specific ICD-10 codes"""
    code = models.CharField("Κωδικός", max_length=10, unique=True, db_index=True)
    label = models.CharField("Περιγραφή", max_length=300)
    category = models.ForeignKey(ICD10Category, on_delete=models.PROTECT, related_name="codes")
    subcategory = models.ForeignKey(ICD10Subcategory, on_delete=models.PROTECT, related_name="codes", null=True, blank=True)
    
    # Additional metadata
    is_active = models.BooleanField("Ενεργός", default=True)
    is_common = models.BooleanField("Συχνός", default=False, help_text="Συχνά χρησιμοποιούμενος κωδικός")
    notes = models.TextField("Σημειώσεις", blank=True)
    
    class Meta:
        ordering = ("code",)
        verbose_name = "ICD-10 Κωδικός"
        verbose_name_plural = "ICD-10 Κωδικοί"
    
    def __str__(self):
        return f"{self.code} - {self.label}"
    
    @property
    def full_hierarchy(self):
        """Get full hierarchical display"""
        if self.subcategory:
            return f"{self.category.name} → {self.subcategory.name} → {self.code}"
        return f"{self.category.name} → {self.code}"


