from django.utils.functional import SimpleLazyObject

from .models import Notification


def _get_notifications_for_user(user):
    """Return a queryset scoped to the current user or an empty queryset when anonymous."""
    if not user.is_authenticated:
        return Notification.objects.none()
    return Notification.objects.filter(user=user)


class NotificationMiddleware:
    """Expose lazy notification helpers on the request object."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lazy_notifications = SimpleLazyObject(lambda: _get_notifications_for_user(request.user))
        request.notifications = lazy_notifications
        request.unread_notifications_count = SimpleLazyObject(
            lambda: lazy_notifications.filter(is_read=False).count()
        )
        response = self.get_response(request)
        return response
