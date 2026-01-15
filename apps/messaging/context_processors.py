# apps/messages/context_processors.py
from django.db.models import Q, Count
from .models import Message


def unread_messages_count(request):
    """
    Add unread messages count to all template contexts
    Usage in templates: {{ unread_messages_count }}
    """
    if request.user.is_authenticated:
        unread_count = Message.objects.filter(
            conversation__participants=request.user
        ).exclude(
            sender=request.user
        ).exclude(
            read_by=request.user
        ).count()
        
        return {
            'unread_messages_count': unread_count
        }
    return {
        'unread_messages_count': 0
    }