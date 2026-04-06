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
    """Get first item from list or return default."""
    if isinstance(value, list) and len(value) > 0:
        return value[0]
    return value


@register.filter
def trend_class(value):
    """Return CSS class based on trend value."""
    try:
        val = float(value)
        if val > 0:
            return 'positive'
        elif val < 0:
            return 'negative'
        return 'neutral'
    except (ValueError, TypeError):
        return 'neutral'


@register.filter
def abs_value(value):
    """Return absolute value."""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, max_value=100):
    """Calculate percentage."""
    try:
        return (float(value) / float(max_value)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def format_duration(minutes):
    """Format duration in minutes to human readable."""
    try:
        minutes = int(minutes)
        hours = minutes // 60
        mins = minutes % 60
        
        if hours and mins:
            return f"{hours}h {mins}m"
        elif hours:
            return f"{hours}h"
        else:
            return f"{mins}m"
    except (ValueError, TypeError):
        return "N/A"


@register.filter
def score_color_class(score):
    """Return color class based on score value."""
    try:
        score = float(score)
        if score >= 90:
            return 'text-green-400'
        elif score >= 80:
            return 'text-blue-400'
        elif score >= 70:
            return 'text-yellow-400'
        elif score >= 60:
            return 'text-orange-400'
        else:
            return 'text-red-400'
    except (ValueError, TypeError):
        return 'text-gray-400'


@register.filter
def badge_count(stats_dict):
    """Count earned badges based on stats."""
    count = 0
    try:
        if stats_dict.get('total_sessions', 0) >= 1:
            count += 1
        if stats_dict.get('total_sessions', 0) >= 5:
            count += 1
        if stats_dict.get('total_sessions', 0) >= 10:
            count += 1
        if stats_dict.get('total_sessions', 0) >= 25:
            count += 1
        if stats_dict.get('perfect_score', False):
            count += 1
        if stats_dict.get('current_streak', 0) >= 7:
            count += 1
        if stats_dict.get('average_score', 0) >= 90:
            count += 1
        if stats_dict.get('score_trend', 0) > 10:
            count += 1
        if stats_dict.get('categories_practiced', 0) >= 5:
            count += 1
    except (AttributeError, TypeError):
        pass
    return count


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def multiply(value, arg):
    """Multiply two values."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Divide two values."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def index(value, i):
    """Get item at index from list."""
    try:
        return value[int(i)]
    except (IndexError, TypeError, ValueError):
        return None


@register.simple_tag
def progress_percentage(current, total):
    """Calculate progress percentage."""
    try:
        if total == 0:
            return 0
        return min(100, int((float(current) / float(total)) * 100))
    except (ValueError, TypeError, ZeroDivisionError):
        return 0



