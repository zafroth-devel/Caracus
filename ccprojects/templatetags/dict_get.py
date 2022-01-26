from django import template
from django.template.defaultfilters import stringfilter
register = template.Library()

@register.filter
def hash(h, key):
    return h[key]

@register.filter(name='splits')
@stringfilter
def split_str(value,arg):
    return value.split('/')[arg]