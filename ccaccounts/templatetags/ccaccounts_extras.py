from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name="addstr")
@stringfilter
def addstr(arg1, arg2):
    return str(arg1) + str(arg2)
