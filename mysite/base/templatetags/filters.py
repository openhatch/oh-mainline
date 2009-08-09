from django import template
from django.utils.timesince import timesince

register = template.Library()

@register.filter
def timesince_terse(value, arg):
    string = timesince(value, arg)
    return string.split(", ")[0]
