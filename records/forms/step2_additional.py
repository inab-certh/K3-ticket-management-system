from django import forms
from records.models import Beneficiary
from django.core.exceptions import ValidationError
from .step2_contact import ContactPersonForm


class BeneficiaryExtraForm(forms.ModelForm):
    class Meta:
        model = Beneficiary
        fields = [
            'gender', 'birth_year', 'marital_status', 'num_children', 'nationality',
            'citizenship', 'health_id', 'landline', 'address', 'vat', 'id_card',
            'city', 'postal_code', 'mobile', 'email',
            'minor_children', 'student_children', 'no_military_obligation'
        ]
        widgets = {
            'birth_year': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'num_children': forms.NumberInput(attrs={'min': 0}),
            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'vat': forms.TextInput(attrs={
                'pattern': r'\d{9}',
                'title': 'Ο ΑΦΜ πρέπει να έχει ακριβώς 9 ψηφία.',
                'class': 'form-control'
            }),
            'health_id': forms.TextInput(attrs={
                'pattern': r'\d{11}',
                'title': 'Ο ΑΜΚΑ πρέπει να έχει ακριβώς 11 ψηφία.',
                'class': 'form-control'
            }),
            'id_card': forms.TextInput(attrs={
                'pattern': r'[A-Z]{2}\d{6}',
                'title': 'Η ταυτότητα πρέπει να έχει 2 κεφαλαία γράμματα και 6 αριθμούς.',
                'class': 'form-control'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        instance = self.instance

        # Fill the instance with cleaned data temporarily for validation
        for field in self.fields:
            setattr(instance, field, cleaned_data.get(field))

        try:
            instance.full_clean(validate_unique=False)
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                if field in self.fields:  # ✅ πρόσθεσε έλεγχο αν το πεδίο υπάρχει στο form
                    for error in errors:
                        self.add_error(field, error)


        num_children = cleaned_data.get("num_children")

        # These fields must be filled if num_children > 0
        if num_children and num_children > 0:
            required_if_children = ['minor_children', 'student_children', 'no_military_obligation']
            for field in required_if_children:
                if cleaned_data.get(field) is None:
                    self.add_error(field, "Αυτό το πεδίο είναι υποχρεωτικό όταν υπάρχουν παιδιά.")

        return cleaned_data
