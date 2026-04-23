# records/forms/action.py
from django import forms
from records.models import Action

class ActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = [
            'action_type', 'direction',
            'action_date',
            'org_name', 'contact_name', 'contact_role',
            'contact_phone', 'contact_email',
            'result',
            'follow_up_date', 'is_completed',
        ]
        widgets = {
            'action_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'result': forms.Textarea(attrs={'rows': 3}),
        }