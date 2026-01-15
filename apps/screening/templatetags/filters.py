from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary by key.
    Usage: {{ dictionary|get_item:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def attr(obj, attribute):
    """
    Get an attribute from an object.
    Usage: {{ object|attr:"attribute_name" }}
    """
    try:
        return getattr(obj, attribute)
    except AttributeError:
        return None
