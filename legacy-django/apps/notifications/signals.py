from django.dispatch import Signal, receiver

from .models import Notification, NotificationType

notification_create = Signal()


@receiver(notification_create)
def _create_notification(sender, user=None, title=None, message=None, link=None,
                         notification_type=None, action_text=None, **kwargs):
    """Persist a notification record whenever the signal is emitted."""
    if not user:
        return

    default_title = Notification._meta.get_field('title').default
    Notification.objects.create(
        user=user,
        title=title or default_title,
        message=message or '',
        notification_type=notification_type or NotificationType.SYSTEM,
        action_url=link,
        action_text=action_text,
    )
