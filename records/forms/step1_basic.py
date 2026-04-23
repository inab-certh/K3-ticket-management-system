# forms/step1_basic.py
from django import forms
from records.models import Request, Beneficiary

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ["structure", "submission_date", "communication_method",
            "contacted_by", "topic", "source_of_info", "protocol_number",
            "accepted_request", "priority", "assigned_to"]
        widgets = {
            'submission_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            })}            
        
class BeneficiaryForm(forms.ModelForm):
    class Meta:        
        model = Beneficiary
        fields = ["last_name", "first_name", "father_name", "mother_name"]
