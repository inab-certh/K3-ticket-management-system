from django import forms
from records.models import MedicalHistory, Comorbidity, Person

class Step5MedicalHistoryForm(forms.ModelForm):
    class Meta:
        model = MedicalHistory
        fields = ['disability', 'certified_disability', 'disability_percentage', 'kepa_check', 'kepa_expiry']
        widgets = {
            'kepa_expiry': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }

class Step5ComorbidityForm(forms.ModelForm):
    class Meta:
        model = Comorbidity
        fields = ['arterial_disease', 'cardiovascular_disease', 'copd', 'diabetes',
                  'psychiatric_disorder', 'mobility_issues', 'nephropathy', 'other_conditions']

class Step5BMIForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['weight', 'height']