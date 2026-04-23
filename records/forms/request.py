# records/forms/request.py
from django import forms
from django.utils import timezone
from records.models import Request

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = [
            "person",
            "center",
            "category",
            "status",
            "priority",
            "tags",
            "communication_method",
            "contact_person_type",
            "subject",
            "submission_date",
            "due_date",
            "expiry_date",
            "closed_date",
            "protocol_number",
            "is_accepted",
            "assigned_to",
        ]
        widgets = {
            "submission_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
            "closed_date": forms.DateInput(attrs={"type": "date"}),
            "tags": forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned = super().clean()
        submitted = cleaned.get("submission_date")
        due = cleaned.get("due_date")
        closed = cleaned.get("closed_date")
        status = cleaned.get("status")

        if submitted and due and due < submitted:
            raise forms.ValidationError("Η προθεσμία δεν μπορεί να είναι πριν την ημερομηνία αίτησης.")
        if submitted and closed and closed < submitted:
            raise forms.ValidationError("Η ημερομηνία κλεισίματος δεν μπορεί να είναι πριν την αίτηση.")
        return cleaned
