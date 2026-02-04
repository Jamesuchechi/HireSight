from django import template
import json

register = template.Library()

@register.filter
def parse_json_field(value, key=None):
    """Safely parse JSON fields and extract values."""
    if not value:
        return ''
    
    # If already a dict/list, use directly
    if isinstance(value, (dict, list)):
        data = value
    else:
        # Try to parse as JSON
        try:
            data = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return str(value)
    
    # If key specified, extract it
    if key and isinstance(data, dict):
        return data.get(key, '')
    
    # If it's a list, join items
    if isinstance(data, list):
        return ', '.join(str(item) for item in data)
    
    return str(data)

@register.filter
def first_item(value):
    """Get first item from list or return value."""
    if isinstance(value, list) and value:
        return value[0]
    return value