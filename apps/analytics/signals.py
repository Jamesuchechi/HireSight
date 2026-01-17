"""
Signal handlers for automatic analytics tracking.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .utils import log_user_activity


# Track resume uploads
@receiver(post_save, sender='resumes.Resume')
def track_resume_upload(sender, instance, created, **kwargs):
    """Track when a user uploads a resume."""
    if created and getattr(instance, 'applicant', None):
        log_user_activity(
            user=instance.applicant,
            action_type='resume_upload',
            metadata={'resume_id': str(instance.id), 'filename': instance.original_filename}
        )


# Track job applications
@receiver(post_save, sender='applications.Application')
def track_job_application(sender, instance, created, **kwargs):
    """Track when a user applies for a job."""
    applicant = getattr(instance, 'applicant', None)
    if created and applicant:
        log_user_activity(
            user=applicant,
            action_type='job_apply',
            metadata={
                'application_id': str(instance.id),
                'job_id': str(instance.job.id),
                'job_title': instance.job.title
            }
        )


# Track job posts
@receiver(post_save, sender='jobs.Job')
def track_job_post(sender, instance, created, **kwargs):
    """Track when a company posts a job."""
    if created and instance.company and hasattr(instance.company, 'user'):
        log_user_activity(
            user=instance.company.user,
            action_type='job_post',
            metadata={
                'job_id': str(instance.id),
                'job_title': instance.title,
                'location': instance.location
            }
        )


# Track profile updates
@receiver(post_save, sender='accounts.PersonalProfile')
def track_personal_profile_update(sender, instance, created, **kwargs):
    """Track personal profile updates."""
    if not created and instance.user:
        log_user_activity(
            user=instance.user,
            action_type='profile_update',
            metadata={'profile_type': 'personal'}
        )


@receiver(post_save, sender='accounts.CompanyProfile')
def track_company_profile_update(sender, instance, created, **kwargs):
    """Track company profile updates."""
    if not created and instance.user:
        log_user_activity(
            user=instance.user,
            action_type='profile_update',
            metadata={'profile_type': 'company'}
        )


# Track follows
@receiver(post_save, sender='following.Follow')
def track_follow(sender, instance, created, **kwargs):
    """Track when a user follows someone."""
    if created and instance.follower:
        log_user_activity(
            user=instance.follower,
            action_type='follow',
            metadata={
                'following_id': str(instance.following.id),
                'following_type': instance.following_type
            }
        )


@receiver(post_delete, sender='following.Follow')
def track_unfollow(sender, instance, **kwargs):
    """Track when a user unfollows someone."""
    if instance.follower:
        log_user_activity(
            user=instance.follower,
            action_type='unfollow',
            metadata={
                'following_id': str(instance.following.id),
                'following_type': instance.following_type
            }
        )


# Track messages
@receiver(post_save, sender='messaging.Message')
def track_message_sent(sender, instance, created, **kwargs):
    """Track when a message is sent."""
    if created and instance.sender:
        log_user_activity(
            user=instance.sender,
            action_type='message_sent',
            metadata={
                'message_id': str(instance.id),
                'receiver_id': str(instance.receiver.id)
            }
        )
