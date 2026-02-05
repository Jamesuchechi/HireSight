from django import template
import json

register = template.Library()

@register.filter
def abs(value):
    return abs(value)


