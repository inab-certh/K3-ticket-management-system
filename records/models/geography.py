from django.db import models

class Region(models.Model):
    """Περιφέρειες - 13 main regions of Greece"""
    name = models.CharField("Περιφέρεια", max_length=100, unique=True)
    code = models.CharField("Κωδικός", max_length=100, unique=True)
    sort_order = models.PositiveIntegerField("Σειρά", default=0)
    
    class Meta:
        ordering = ("sort_order", "name")
        verbose_name = "Περιφέρεια"
        verbose_name_plural = "Περιφέρειες"
    
    def __str__(self):
        return self.name


class RegionalUnit(models.Model):
    """Περιφερειακές Ενότητες - Regional units within regions"""
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="regional_units")
    name = models.CharField("Περιφερειακή Ενότητα", max_length=100)
    sort_order = models.PositiveIntegerField("Σειρά", default=0)
    
    class Meta:
        ordering = ("region", "sort_order", "name")
        unique_together = ("region", "name")
        verbose_name = "Περιφερειακή Ενότητα"
        verbose_name_plural = "Περιφερειακές Ενότητες"
    
    def __str__(self):
        return f"{self.name} ({self.region.name})"


class Municipality(models.Model):
    """Δήμοι - Municipalities within regional units"""
    regional_unit = models.ForeignKey(RegionalUnit, on_delete=models.CASCADE, related_name="municipalities")
    name = models.CharField("Δήμος", max_length=100)
    sort_order = models.PositiveIntegerField("Σειρά", default=0)
    
    # Computed fields for easier access
    @property
    def region(self):
        return self.regional_unit.region
    
    class Meta:
        ordering = ("regional_unit", "sort_order", "name")
        unique_together = ("regional_unit", "name")
        verbose_name = "Δήμος"
        verbose_name_plural = "Δήμοι"
    
    def __str__(self):
        return self.name
    
    def get_full_name(self):
        """Get full hierarchical name"""
        return f"{self.name}, {self.regional_unit.name}, {self.region.name}"


