# records/templatetags/k3_tags.py
from django import template

register = template.Library()

TAG_CATEGORY_LABELS = {
    'kepa': 'ΚΕΠΑ',
    'benefits': 'Επιδόματα/Παροχές',
    'disability': 'Αναπηρία',
    'work': 'Εργασιακά',
    'education': 'Εκπαίδευση',
    'medical': 'Ιατρικές Υπηρεσίες',
    'psychosocial': 'Ψυχοκοινωνική Υποστήριξη',
    'transport': 'Μετακίνηση',
    'accommodation': 'Φιλοξενία',
    'financial': 'Οικονομική Υποστήριξη',
    'administrative': 'Διοικητικές Διαδικασίες',
}

@register.filter
def category_label(value):
    return TAG_CATEGORY_LABELS.get(value, value)