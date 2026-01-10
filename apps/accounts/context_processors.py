from django.utils import timezone


def unread_notifications_count(request):
    """Context processor to add unread notifications count to all templates."""
    if request.user.is_authenticated:
        try:
            # Get count of unread notifications
            count = request.user.notifications.filter(is_read=False).count()
        except AttributeError:
            # Handle case where notifications relationship doesn't exist yet
            count = 0
    else:
        count = 0

    return {
        'unread_notifications_count': count,
    }