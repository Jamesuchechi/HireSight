from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse


@shared_task
def send_follow_notification(follower_id, followed_id):
    """
    Send email notification when someone follows a user.
    Runs asynchronously via Celery.
    """
    from apps.accounts.models import User
    from .models import Follow
    
    try:
        follower = User.objects.select_related(
            'personalprofile', 'companyprofile'
        ).get(id=follower_id)
        
        followed = User.objects.get(id=followed_id)
        
        preferences = getattr(followed, 'email_preferences', None)
        if preferences and 'new_follower' not in preferences.get_enabled_notifications():
            return f"{followed.email} has disabled new follower emails"
        
        # Check if user has email notifications enabled
        # (assumes you have a preferences system)
        # Prepare email context
        follower_profile = getattr(follower, 'personalprofile', None)
        company_profile = getattr(follower, 'companyprofile', None)
        follower_headline = (
            (getattr(follower_profile, 'headline', None) if follower.account_type == 'personal' else None) or
            (company_profile.industry if company_profile else None) or
            'HireSight member'
        )

        context = {
            'follower': follower,
            'followed': followed,
            'follower_name': follower.get_display_name(),
            'follower_headline': follower_headline,
            'profile_url': f"{settings.SITE_URL}{reverse('accounts:profile_detail', kwargs={'user_id': follower.id})}",
            'manage_preferences_url': f"{settings.SITE_URL}{reverse('accounts:email_preferences')}",
            'site_name': 'HireSight',
        }
        
        # Render email templates
        subject = f'{context["follower_name"]} started following you on HireSight'
        html_message = render_to_string('following/emails/new_follower.html', context)
        plain_message = render_to_string('following/emails/new_follower.txt', context)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[followed.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Mark notification as sent
        Follow.objects.filter(
            follower=follower,
            followed=followed
        ).update(notification_sent=True)
        
        return f"Notification sent to {followed.email}"
        
    except User.DoesNotExist:
        return "User not found"
    except Exception as e:
        # Log error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send follow notification: {str(e)}")
        raise


@shared_task
def cleanup_orphaned_follows():
    """
    Periodic task to clean up follows where users have been deleted.
    Run this daily via Celery beat.
    """
    from .models import Follow
    from apps.accounts.models import User
    
    # Find follows with non-existent users
    orphaned_follows = Follow.objects.filter(
        follower__isnull=True
    ) | Follow.objects.filter(
        followed__isnull=True
    )
    
    count = orphaned_follows.count()
    orphaned_follows.delete()
    
    return f"Cleaned up {count} orphaned follow relationships"


@shared_task
def calculate_follow_statistics(user_id):
    """
    Calculate and cache follow statistics for a user.
    """
    from apps.accounts.models import User
    from .models import Follow
    from django.core.cache import cache
    
    try:
        user = User.objects.get(id=user_id)
        
        stats = {
            'follower_count': Follow.get_follower_count(user),
            'following_count': Follow.get_following_count(user),
            'mutual_count': Follow.objects.filter(
                follower=user,
                followed__in=Follow.objects.filter(
                    followed=user
                ).values_list('follower', flat=True)
            ).count()
        }
        
        # Cache for 1 hour
        cache.set(f'follow_stats_{user_id}', stats, 3600)
        
        return stats
        
    except User.DoesNotExist:
        return None


@shared_task
def bulk_follow_users(follower_id, user_ids_to_follow):
    """
    Bulk follow multiple users.
    Used for CSV import and bulk operations.
    """
    from apps.accounts.models import User
    from .models import Follow
    
    try:
        follower = User.objects.get(id=follower_id)
        
        # Validate follower can follow
        if follower.account_type == 'company':
            return {'error': 'Company accounts cannot follow users'}
        
        results = {
            'success': [],
            'already_following': [],
            'errors': []
        }
        
        for user_id in user_ids_to_follow:
            try:
                user_to_follow = User.objects.get(id=user_id)
                
                # Check if already following
                if Follow.objects.filter(
                    follower=follower,
                    followed=user_to_follow
                ).exists():
                    results['already_following'].append(user_id)
                    continue
                
                # Create follow
                Follow.objects.create(
                    follower=follower,
                    followed=user_to_follow
                )
                results['success'].append(user_id)
                
            except User.DoesNotExist:
                results['errors'].append(f"User {user_id} not found")
            except Exception as e:
                results['errors'].append(f"Error following {user_id}: {str(e)}")
        
        return results
        
    except User.DoesNotExist:
        return {'error': 'Follower not found'}


@shared_task(bind=True)
def process_bulk_follow_operation(self, follower_id, user_ids, action='follow', operation_id=None):
    """
    Process a queued bulk follow job with progress tracking and notifications.
    """
    from django.core.cache import cache
    from django.utils import timezone
    import logging

    from apps.accounts.models import User
    from .models import Follow, Activity, ActivityType
    from apps.notifications.models import Notification, NotificationType

    logger = logging.getLogger(__name__)
    progress_key = f'bulk_follow_progress_{follower_id}'
    result_key = f'bulk_follow_result_{follower_id}'

    cache.set(progress_key, {
        'status': 'processing',
        'action': action,
        'operation_id': operation_id,
        'processed': 0,
        'total': len(user_ids),
        'success': 0,
        'errors': [],
        'timestamp': timezone.now().isoformat()
    }, 3600)

    try:
        follower = User.objects.get(id=follower_id)
    except User.DoesNotExist:
        cache.set(progress_key, {'status': 'failed', 'message': 'Follower not found'})
        return {'error': 'Follower not found'}

    unique_ids = list(dict.fromkeys(user_ids))
    batch_size = 10
    success_count = 0
    already_count = 0
    errors = []

    for idx, target_id in enumerate(unique_ids, start=1):
        try:
            target = User.objects.get(id=target_id)
            if target == follower:
                errors.append("Cannot follow yourself.")
            elif Follow.objects.filter(follower=follower, followed=target).exists():
                already_count += 1
            else:
                Follow.objects.create(follower=follower, followed=target)
                success_count += 1
        except User.DoesNotExist:
            errors.append(f"User {target_id} not found")
        except Exception as exc:
            logger.error("Bulk follow error: %s", exc)
            errors.append(f"Failed on {target_id}: {str(exc)}")

        if idx % batch_size == 0 or idx == len(unique_ids):
            cache.set(progress_key, {
                'status': 'processing' if idx < len(unique_ids) else 'complete',
                'action': action,
                'operation_id': operation_id,
                'processed': idx,
                'total': len(unique_ids),
                'success': success_count,
                'already': already_count,
                'errors': errors[-10:],
                'timestamp': timezone.now().isoformat()
            }, 3600)

    Activity.objects.create(
        user=follower,
        activity_type=ActivityType.BULK_OPERATION,
        content={
            'action': action,
            'processed': len(unique_ids),
            'successful': success_count,
            'errors': len(errors)
        }
    )

    Notification.objects.create(
        user=follower,
        title="Bulk follow operation complete",
        message=f"Processed {len(unique_ids)} users with {success_count} new follows.",
        notification_type=NotificationType.SYSTEM,
        action_url=reverse('following:bulk_follow'),
        action_text="View bulk operations"
    )

    cache.set(result_key, {
        'status': 'finished',
        'action': action,
        'processed': len(unique_ids),
        'success': success_count,
        'already': already_count,
        'errors': errors
    }, 3600)

    manage_preferences_url = f"{settings.SITE_URL}{reverse('accounts:email_preferences')}"
    profile_url = f"{settings.SITE_URL}{reverse('following:bulk_follow')}"
    subject = 'HireSight bulk follow summary'
    plain_message = (
        f"Hi {follower.get_display_name()},\n\n"
        f"Your bulk follow operation completed. "
        f"{success_count} new follows were created and {already_count} accounts were already in your network. "
        f"{len(errors)} items encountered issues.\n\n"
        f"View details: {profile_url}\n"
        f"Manage preferences: {manage_preferences_url}\n\n"
        f"Thanks,\nHireSight Team"
    )

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[follower.email],
        fail_silently=True,
    )

    return {
        'success': success_count,
        'already': already_count,
        'errors': errors
    }
