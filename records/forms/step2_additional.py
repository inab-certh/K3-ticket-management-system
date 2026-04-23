from django import forms
from records.models import Person
from django.core.exceptions import ValidationError

class BeneficiaryExtraForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            'gender', 'birth_year', 'marital_status', 'children_count', 'nationality',
            'citizenship', 'amka', 'landline', 'address', 'vat', 'id_card',
            'city', 'postal_code', 'mobile', 'email',
            'minors', 'students', 'no_military_service'
        ]
        widgets = {
            'birth_year': forms.NumberInput(attrs={'min': 1900, 'max': 2100, 'class': 'form-control'}),
            'children_count': forms.NumberInput(attrs={'min': 0}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'vat': forms.TextInput(attrs={
                'pattern': r'\d{9}',
                'title': 'Ο ΑΦΜ πρέπει να έχει ακριβώς 9 ψηφία.',
                'class': 'form-control'
            }),
            'amka': forms.TextInput(attrs={
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
        children = cleaned_data.get("children_count") or 0
        minors = cleaned_data.get("minors") or 0
        students = cleaned_data.get("students") or 0
        military = cleaned_data.get("no_military_service") or 0

        if children > 0:
            if minors > children:
                self.add_error("minors", f"Δεν μπορεί να υπερβαίνει τον αριθμό παιδιών ({children}).")
            if students > children:
                self.add_error("students", f"Δεν μπορεί να υπερβαίνει τον αριθμό παιδιών ({children}).")
            if military > children:
                self.add_error("no_military_service", f"Δεν μπορεί να υπερβαίνει τον αριθμό παιδιών ({children}).")
            if minors + students > children:
                self.add_error("students", "Ανήλικα + Φοιτητές δεν μπορεί να υπερβαίνει τον αριθμό παιδιών.")

        return cleaned_data