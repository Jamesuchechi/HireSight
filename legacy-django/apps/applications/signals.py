"""
Signal handlers for application events.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from .models import Application, ApplicationStatusHistory, ApplicationStatus

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Application)
def application_post_save(sender, instance, created, **kwargs):
    """
    Handle post-save events for Application model.
    
    Triggers:
    - Send email notification to applicant (async)
    - Send email notification to company (async)
    - Create notification for company
    - Update job application count
    """
    if created:
        # New application created
        logger.info(f"New application created: {instance.id}")
        
        # Import here to avoid circular imports
        from .tasks import (
            send_application_confirmation_email,
            send_new_application_notification_to_company,
            create_application_notification
        )
        
        # Queue async tasks
        transaction.on_commit(lambda: send_application_confirmation_email.delay(instance.id))
        transaction.on_commit(lambda: send_new_application_notification_to_company.delay(instance.id))
        transaction.on_commit(lambda: create_application_notification.delay(instance.id))


@receiver(pre_save, sender=Application)
def application_status_change(sender, instance, **kwargs):
    """
    Detect status changes and trigger appropriate actions.
    
    Creates status history entry if status changed.
    """
    if instance.pk:
        try:
            old_instance = Application.objects.get(pk=instance.pk)
            
            # Check if status changed
            if old_instance.status != instance.status:
                logger.info(f"Application {instance.id} status changed: {old_instance.status} -> {instance.status}")
                
                # Import here to avoid circular imports
                from .tasks import send_status_update_email
                
                # Queue async task for email notification
                transaction.on_commit(lambda: send_status_update_email.delay(instance.id))
                
        except Application.DoesNotExist:
            pass


@receiver(post_save, sender=ApplicationStatusHistory)
def status_history_created(sender, instance, created, **kwargs):
    """
    Handle creation of status history entries.
    
    Log status changes for audit trail.
    """
    if created:
        logger.info(
            f"Status history created for application {instance.application.id}: "
            f"{instance.old_status} -> {instance.new_status} by {instance.changed_by}"
        )