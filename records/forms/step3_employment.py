from django import forms
from records.models import Person

class Step3Form(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            'insurance_status', 'insurance_provider', 'special_funds',
            'widow_pension', 'disability_pension',
            'status', 'unemployment_card', 'unemployment_registration_date',
            'profession', 'specialization', 'employment_type',
            'employer_legal_form', 'hire_date', 'work_schedule', 'contract_type',
        ]
        widgets = {
            'unemployment_registration_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'hire_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }