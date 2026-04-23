# records/forms/request.py
from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from records.models import Request

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = [
            "person",
            "center",
            "category",
            "request_type",
            "status",
            "priority",
            "subject",
            "description",
            "submitted_at",
            "due_at",
            "expiry_date",
            "closed_at",
            "outcome",
        ]
        widgets = {
            "submitted_at": forms.DateInput(attrs={"type": "date"}),
            "due_at": forms.DateInput(attrs={"type": "date"}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
            "closed_at": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        submitted = cleaned.get("submitted_at")
        due = cleaned.get("due_at")
        closed = cleaned.get("closed_at")
        status = cleaned.get("status")

        if submitted and due and due < submitted:
            raise ValidationError("Η προθεσμία δεν μπορεί να είναι πριν την ημερομηνία αίτησης.")
        if submitted and closed and closed < submitted:
            raise ValidationError("Η ημερομηνία κλεισίματος δεν μπορεί να είναι πριν την αίτηση.")
        # If your RequestStatus has is_closed flag (as we set), enforce closed_at
        if status and getattr(status, "is_closed", False) and not closed:
            raise ValidationError("Για κλειστή κατάσταση απαιτείται ημερομηνία κλεισίματος.")

        return cleaned
