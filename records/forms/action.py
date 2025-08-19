# records/forms/action.py
from django import forms
from records.models import Action

class ActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = [
            "request",
            "person",
            "action_type",
            "channel",
            "when",
            "by_whom",
            "notes",
            "next_due",
        ]
        widgets = {
            "when": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
