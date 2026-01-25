from django.urls import reverse


def notification_dropdown_context(request):
    """Expose recent notifications for the global navbar dropdown."""
    if not request.user.is_authenticated:
        return {}

    notifications_qs = getattr(request, 'notifications', None)
    items = []
    if notifications_qs is not None:
        items = list(notifications_qs.order_by('-created_at')[:5])

    return {
        'notification_dropdown_items': items,
        'notification_list_url': reverse('notifications:list'),
    }
