from django import forms
from django.forms.models import inlineformset_factory
from records.models import Beneficiary, Neoplasm

class NeoplasmForm(forms.ModelForm):
    class Meta:
        model = Neoplasm
        # we’ll set neoplasm_type as hidden and drive it from the view
        fields = ["neoplasm_type", "type", "icd10_code", "localization"]
        widgets = {
            "neoplasm_type": forms.Select(attrs={"class": "form-select"}),
            'type': forms.Select(attrs={'class': 'form-select', 'id': 'type'}),
            #"icd10_code": forms.Select(attrs={"class": "form-select icd10-select", "readonly": "readonly"}),  # Hide by JS
            "icd10_code": forms.HiddenInput(),  # we autofill it, and show the label elsewhere
            "localization": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ελεύθερο κείμενο"}),
        }

# up to 4 malignant
MalignantNeoplasmFormSet = inlineformset_factory(
    Beneficiary,
    Neoplasm,
    form=NeoplasmForm,
    extra=4,
    max_num=4,
    can_delete=True,
    fk_name="beneficiary",
)

# up to 3 benign
BenignNeoplasmFormSet = inlineformset_factory(
    Beneficiary,
    Neoplasm,
    form=NeoplasmForm,
    extra=3,
    max_num=3,
    can_delete=True,
    fk_name="beneficiary",
)

# up to 3 uncertain
UncertainNeoplasmFormSet = inlineformset_factory(
    Beneficiary,
    Neoplasm,
    form=NeoplasmForm,
    extra=3,
    max_num=3,
    can_delete=True,
    fk_name="beneficiary",
)
