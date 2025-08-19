# records/forms/therapy.py
from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from records.models import Therapy

class TherapyForm(forms.ModelForm):
    class Meta:
        model = Therapy
        fields = [
            "neoplasm",
            "therapy_type",
            "hospital_name",
            "start_date",
            "notes",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_start_date(self):
        d = self.cleaned_data.get("start_date")
        if d and d > date.today():
            raise ValidationError("Η ημερομηνία έναρξης δεν μπορεί να είναι μελλοντική.")
        return d

    def clean(self):
        cleaned = super().clean()
        # If notes are empty but hospital is given, that's fine; no extra rules.
        # Add any cross-field checks here if needed later.
        return cleaned
