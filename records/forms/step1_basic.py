# forms/step1_basic.py
from django import forms
from records.models import Person, Request

class BeneficiaryForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ["last_name", "first_name", "father_name", "mother_name", "knowledge_source"]

class Step1RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = [
            "center", "submission_date", "communication_method",
            "contact_person_type", "subject",
            "protocol_number", "is_accepted", "priority", "assigned_to"
        ]
        widgets = {
            'submission_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
        }