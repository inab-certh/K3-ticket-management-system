from django import forms
from records.models.person import Insurance, Employment

class InsuranceForm(forms.ModelForm):
    class Meta:
        model = Insurance
        fields = '__all__'
        exclude = ['beneficiary']

class EmploymentForm(forms.ModelForm):
    class Meta:
        model = Employment
        fields = '__all__'
        exclude = ['beneficiary']
