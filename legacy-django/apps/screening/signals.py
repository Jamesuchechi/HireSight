"""
Signal handlers for screening events.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction

from .models import ScreeningResult, ScreeningSession, ScreeningResultStatus, ScreeningStatus

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ScreeningResult)
def screening_result_post_save(sender, instance, created, **kwargs):
    """Handle post-save events for ScreeningResult."""
    
    if created:
        logger.info(f"New screening result created: {instance.id}")
    
    # If result status changed to completed, update session statistics
    if instance.status == ScreeningResultStatus.COMPLETED:
        transaction.on_commit(
            lambda: update_session_stats(instance.session.id)
        )


@receiver(post_save, sender=ScreeningSession)
def screening_session_post_save(sender, instance, created, **kwargs):
    """Handle post-save events for ScreeningSession."""
    
    if created:
        logger.info(f"New screening session created: {instance.id}")
    
    # If session just completed, send notification
    if instance.status == ScreeningStatus.COMPLETED:
        from .tasks import send_screening_complete_notification
        transaction.on_commit(
            lambda: send_screening_complete_notification.delay(instance.id)
        )


def update_session_stats(session_id):
    """Update session statistics (called as Celery task)."""
    from .tasks import update_session_statistics
    return update_session_statistics.delay(session_id)