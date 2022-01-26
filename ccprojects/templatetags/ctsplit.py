from django import template
from django.template.defaultfilters import stringfilter
register = template.Library()

@register.filter(name='splits')
@stringfilter
def split_str(value):
    return value.split('/')