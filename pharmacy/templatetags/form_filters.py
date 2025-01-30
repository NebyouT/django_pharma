from django import template
from django.forms import CheckboxInput

register = template.Library()

@register.filter
def is_checkbox_field(field):
    return isinstance(field.field.widget, CheckboxInput)

@register.filter
def get_field_type(field):
    return field.field.widget.__class__.__name__
