# records/templatetags/form_extras.py
from django import template
from django.forms.boundfield import BoundField

register = template.Library()

@register.filter(name="add_class")
def add_class(field, css_class):
    """
    Add CSS classes to a bound form field without losing existing widget attrs.
    Usage: {{ form.foo|add_class:"form-control is-invalid" }}
    """
    if not isinstance(field, BoundField):
        return field  # don't crash if someone passes a plain value
    attrs = field.field.widget.attrs.copy()
    existing = attrs.get("class", "")
    attrs["class"] = (existing + " " + css_class).strip() if existing else css_class
    return field.as_widget(attrs=attrs)
