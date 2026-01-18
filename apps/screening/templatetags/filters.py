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


@register.filter
def mul(value, multiplier):
    """
    Multiply a numeric value by another number.
    Usage: {{ value|mul:factor }}
    """
    try:
        return float(value) * float(multiplier)
    except (TypeError, ValueError):
        return ""


@register.filter
def get_index(sequence, index):
    """
    Get an item from a list/tuple by index or fall back to dict lookup.
    Usage: {{ sequence|get_index:index }}
    """
    try:
        idx = int(index)
    except (TypeError, ValueError):
        idx = None

    if isinstance(sequence, (list, tuple)) and idx is not None:
        try:
            return sequence[idx]
        except IndexError:
            return None
    if isinstance(sequence, dict):
        return sequence.get(index)
    return None
