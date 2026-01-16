from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from django.urls import reverse

from apps.notifications.models import Notification, NotificationType
from apps.accounts.models import PersonalProfile, CompanyProfile
from apps.jobs.models import Job, JobStatus

from .models import Follow, Activity, ActivityType


@receiver(post_save, sender=Follow)
def follow_created(sender, instance, created, **kwargs):
    """
    Trigger actions when a new follow relationship is created.
    """
    if created:
        # Clear follower/following count cache
        cache.delete(f'follower_count_{instance.followed.id}')
        cache.delete(f'following_count_{instance.follower.id}')
        
        Notification.objects.create(
            user=instance.followed,
            title='New follower on HireSight',
            message=f'{instance.follower.get_display_name()} started following you',
            notification_type=NotificationType.NEW_FOLLOWER,
            action_url=reverse('accounts:profile_detail', kwargs={'user_id': instance.follower.id}),
            action_text='View profile',
            related_object_id=str(instance.follower.id),
        )

        if not getattr(instance, '_skip_async_notification', False):
            from apps.following.tasks import send_follow_notification

            send_follow_notification.delay(
                follower_id=instance.follower.id,
                followed_id=instance.followed.id
            )

        Activity.objects.create(
            user=instance.follower,
            activity_type=ActivityType.FOLLOWED_USER,
            content={
                'followed_user_id': instance.followed.id,
                'followed_user_name': instance.followed.get_display_name(),
                'followed_user_type': instance.followed.account_type
            }
        )


@receiver(post_delete, sender=Follow)
def follow_deleted(sender, instance, **kwargs):
    """
    Clean up when a follow relationship is deleted.
    """
    # Clear follower/following count cache
    cache.delete(f'follower_count_{instance.followed.id}')
    cache.delete(f'following_count_{instance.follower.id}')
    
    # Optional: Send notification about unfollow (usually not needed)
    # or track in analytics

    Activity.objects.create(
        user=instance.follower,
        activity_type=ActivityType.UNFOLLOWED_USER,
        content={
            'unfollowed_user_id': instance.followed.id,
            'unfollowed_user_name': instance.followed.get_display_name()
        }
    )


def _record_activity(user, activity_type, content=None, is_public=True):
    Activity.objects.create(
        user=user,
        activity_type=activity_type,
        content=content or {},
        is_public=is_public
    )


def _normalize_skill_names(skills):
    names = set()
    for skill in skills or []:
        if isinstance(skill, str):
            value = skill
        elif isinstance(skill, dict):
            value = skill.get('skill') or skill.get('name') or skill.get('label')
        else:
            continue

        if value:
            names.add(value.strip().lower())
    return names


@receiver(post_save, sender=Job)
def job_posted_activity(sender, instance, created, **kwargs):
    if not created or instance.status != JobStatus.ACTIVE:
        return

    company_user = getattr(instance.company, 'user', None)
    if not company_user:
        return

    _record_activity(
        company_user,
        ActivityType.JOB_POSTED,
        content={
            'job_id': str(instance.id),
            'job_title': instance.title,
            'job_slug': instance.slug,
            'location': instance.location,
        }
    )


@receiver(pre_save, sender=PersonalProfile)
def cache_personal_skills(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_skills = []
        return

    try:
        previous = PersonalProfile.objects.get(pk=instance.pk)
        instance._previous_skills = previous.skills or []
    except PersonalProfile.DoesNotExist:
        instance._previous_skills = []


@receiver(post_save, sender=PersonalProfile)
def personal_profile_activity(sender, instance, created, **kwargs):
    if created:
        return

    _record_activity(
        instance.user,
        ActivityType.PROFILE_UPDATED,
        content={'headline': instance.headline}
    )

    previous_skills = _normalize_skill_names(getattr(instance, '_previous_skills', []))
    current_skills = _normalize_skill_names(getattr(instance, 'skills', []))
    added_skills = sorted(current_skills - previous_skills)

    if added_skills:
        _record_activity(
            instance.user,
            ActivityType.SKILL_ADDED,
            content={'added_skills': added_skills}
        )


@receiver(post_save, sender=CompanyProfile)
def company_profile_activity(sender, instance, created, **kwargs):
    if created:
        return

    _record_activity(
        instance.user,
        ActivityType.PROFILE_UPDATED,
        content={'company_name': instance.company_name}
    )
