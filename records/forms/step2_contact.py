from django import forms
from records.models import ContactPerson

class ContactPersonForm(forms.ModelForm):
    class Meta:
        model = ContactPerson
        fields = ['first_name', 'last_name', 'relation', 'email', 'mobile', 'landline', 'city', 'postal_code', 'municipality', 'address']
