# records/forms/neoplasm.py
from django import forms
from django.core.exceptions import ValidationError
from records.models import Neoplasm

class NeoplasmForm(forms.ModelForm):
    class Meta:
        model = Neoplasm
        fields = [
            "person",
            "neoplasm_type",
            "type",
            "icd10_code",
            "localization",
            "metastasis",
            "surgery",
            "surgery_hospital",
            "scheduled_treatment",
        ]
        widgets = {
            "scheduled_treatment": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        person = cleaned.get("person")
        neoplasm_type = cleaned.get("neoplasm_type")
        surgery = cleaned.get("surgery")
        surgery_hospital = cleaned.get("surgery_hospital")

        # enforce surgery rule
        if surgery and not surgery_hospital:
            raise ValidationError("Αν έχει γίνει χειρουργείο, πρέπει να δηλωθεί το νοσοκομείο.")

        # max 4 per person+category
        if person and neoplasm_type:
            qs = Neoplasm.objects.filter(person=person, neoplasm_type=neoplasm_type)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.count() >= 4:
                raise ValidationError("Ένα άτομο μπορεί να έχει μέχρι 4 νεοπλάσματα ανά κατηγορία.")

        return cleaned
