from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Interview, InterviewActivityLog
from .models import InterviewPracticeSession
from django.core.cache import cache
import json
import hashlib
from apps.applications.models import ApplicationStatus


@receiver(pre_save, sender=Interview)
def track_interview_changes(sender, instance, **kwargs):
    """
    Track changes to interview before saving
    Used for detecting reschedules and status changes
    """
    if instance.pk:
        try:
            old_instance = Interview.objects.get(pk=instance.pk)
            
            # Track if scheduled date changed (reschedule)
            if old_instance.scheduled_date != instance.scheduled_date:
                if not instance.original_scheduled_date:
                    instance.original_scheduled_date = old_instance.scheduled_date
            
            # Keep previous status for post_save signal
            instance._previous_status = old_instance.status
        except Interview.DoesNotExist:
            pass
    else:
        instance._previous_status = None


@receiver(post_save, sender=Interview)
def update_application_status_on_interview_save(sender, instance, created, **kwargs):
    """
    Automatically update application status when interview is created or updated
    """
    application = instance.application
    
    # When interview is created, set application to INTERVIEW status
    if created and application.status != ApplicationStatus.INTERVIEW:
        application.status = ApplicationStatus.INTERVIEW
        application.save(update_fields=['status'])
    
    # When interview is completed, potentially move to next stage
    if instance.status == Interview.InterviewStatus.COMPLETED:
        # Check if there's a positive rating
        if instance.interview_rating and instance.interview_rating >= 4:
            # Could automatically move to OFFER stage if this was final interview
            # For now, just ensure it stays in INTERVIEW
            if application.status not in [ApplicationStatus.OFFER, ApplicationStatus.HIRED]:
                application.status = ApplicationStatus.INTERVIEW
                application.save(update_fields=['status'])
    
    # When interview is cancelled, move back to screening if no other interviews
    elif instance.status == Interview.InterviewStatus.CANCELLED:
        # Check if there are other active interviews
        other_interviews = Interview.objects.filter(
            application=application
        ).exclude(
            pk=instance.pk
        ).exclude(
            status__in=[Interview.InterviewStatus.CANCELLED, Interview.InterviewStatus.COMPLETED]
        )
        
        if not other_interviews.exists():
            # No other active interviews, move back to screening
            if application.status == ApplicationStatus.INTERVIEW:
                application.status = ApplicationStatus.SCREENING
                application.save(update_fields=['status'])
    
    # When candidate is marked as no-show
    elif instance.status == Interview.InterviewStatus.NO_SHOW:
        metadata = {
            'candidate_response': instance.candidate_response,
            'contacted_candidate': getattr(instance, 'no_show_contacted_candidate', False),
            'reschedule_count': instance.reschedule_count,
        }
        actor = getattr(instance, '_activity_actor', None)
        InterviewActivityLog.objects.create(
            interview=instance,
            action=InterviewActivityLog.ActionChoices.NO_SHOW,
            notes=instance.completion_notes,
            metadata=metadata,
            recorded_by=actor
        )


@receiver(post_save, sender=Interview)
def create_notification_on_interview_action(sender, instance, created, **kwargs):
    """
    Create notifications for interview-related actions
    Requires notifications app to be installed
    """
    previous_status = getattr(instance, '_previous_status', None)

    try:
        from apps.notifications.models import Notification
        
        if created:
            # Notify candidate of new interview
            Notification.objects.create(
                user=instance.application.applicant,
                    notification_type='INTERVIEW_SCHEDULED',
                    title='Interview Scheduled',
                    message=f'You have an interview scheduled for {instance.application.job.title} '
                            f'on {instance.scheduled_date.strftime("%B %d, %Y at %I:%M %p")}',
                    action_url=f'/interviews/{instance.id}/'
                )
            
            # Notify company/recruiter
            Notification.objects.create(
                user=instance.application.job.company.user,
                notification_type='INTERVIEW_SCHEDULED',
                title='Interview Scheduled',
                message=f'Interview scheduled with {instance.application.applicant.email} '
                        f'for {instance.application.job.title}',
                action_url=f'/interviews/{instance.id}/'
            )
        
        elif previous_status != instance.status:
            if instance.status == Interview.InterviewStatus.RESCHEDULED:
                Notification.objects.create(
                    user=instance.application.applicant,
                    notification_type='INTERVIEW_RESCHEDULED',
                    title='Interview Rescheduled',
                    message=f'Your interview for {instance.application.job.title} has been rescheduled',
                    action_url=f'/interviews/{instance.id}/'
                )
            elif instance.status == Interview.InterviewStatus.CANCELLED:
                Notification.objects.create(
                    user=instance.application.applicant,
                    notification_type='INTERVIEW_CANCELLED',
                    title='Interview Cancelled',
                    message=f'Your interview for {instance.application.job.title} has been cancelled',
                    action_url=f'/applications/{instance.application.id}/'
                )
            elif instance.status == Interview.InterviewStatus.COMPLETED:
                Notification.objects.create(
                    user=instance.application.applicant,
                    notification_type='INTERVIEW_COMPLETED',
                    title='Interview Completed',
                    message=f'Your interview for {instance.application.job.title} has been marked as completed',
                    action_url=f'/applications/{instance.application.id}/'
                )
    
    except ImportError:
        # Notifications app not installed, skip
        pass


@receiver(post_save, sender=InterviewPracticeSession)
def clear_practice_session_cache(sender, instance, **kwargs):
    """Clear related AI cache entries when a practice session is updated."""
    # Clear report cache
    try:
        cache.delete(f"ai:report:session:{instance.id}")
    except Exception:
        pass

    # Clear question generation cache for this session settings if present
    try:
        key_source = json.dumps({
            'candidate': getattr(instance.candidate, 'id', None),
            'application': getattr(instance.application, 'id', None),
            'settings': instance.settings or {}
        }, sort_keys=True, default=str)
        cache_key = 'ai:questions:' + hashlib.sha256(key_source.encode('utf-8')).hexdigest()
        cache.delete(cache_key)
    except Exception:
        pass
