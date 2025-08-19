# records/forms/person.py
from django import forms
from records.models import Person
from records.utils import greek_upper_no_tone

class GreekNormalizeMixin:
    """
    Reusable normalizer for Greek fields: uppercase, no tonos, trimmed.
    Add field names to NORMALIZE_FIELDS to auto-normalize them.
    """
    NORMALIZE_FIELDS = ()

    def _normalize_value(self, value):
        return greek_upper_no_tone(value)

    def clean(self):
        cleaned = super().clean()
        for fname in getattr(self, "NORMALIZE_FIELDS", ()):
            if fname in cleaned:
                cleaned[fname] = self._normalize_value(cleaned.get(fname))
        return cleaned


class PersonForm(GreekNormalizeMixin, forms.ModelForm):
    # Choose which fields to normalize automatically
    NORMALIZE_FIELDS = (
        "last_name",
        "first_name",
        "father_name",
        "mother_name",
        "id_card",
    )

    class Meta:
        model = Person
        fields = [
            "last_name",
            "first_name",
            "father_name",
            "mother_name",
            "birth_date",
            "age",
            "gender",
            "nationality",
            "citizenship",
            "vat",
            "amka",
            "id_card",
            "landline",
            "mobile",
            "email",
            "address",
            "postal_code",
            "municipality",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
