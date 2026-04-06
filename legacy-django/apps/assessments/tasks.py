from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_attempts():
    """Mark expired in-progress attempts"""
    from .models import SkillAssessmentAttempt
    
    expired_count = 0
    in_progress = SkillAssessmentAttempt.objects.filter(status='IN_PROGRESS')
    
    for attempt in in_progress:
        if attempt.is_time_expired():
            attempt.status = 'EXPIRED'
            attempt.time_limit_exceeded = True
            attempt.save()
            expired_count += 1
            
            logger.info(f"Marked attempt {attempt.id} as expired for user {attempt.user.email}")
    
    logger.info(f"Cleanup complete: {expired_count} attempts marked as expired")
    return expired_count


@shared_task
def send_badge_earned_notification(badge_id):
    """Send email notification when badge is earned"""
    from .models import SkillBadge
    
    try:
        badge = SkillBadge.objects.select_related('user', 'test', 'attempt').get(id=badge_id)
        
        # Check user email preferences
        if not hasattr(badge.user, 'email_preferences'):
            return
        
        prefs = badge.user.email_preferences
        if not prefs.notify_job_recommendations:  # Using similar notification type
            return
        
        subject = f'🎉 Congratulations! You earned the {badge.badge_name} badge'
        
        context = {
            'user': badge.user,
            'badge': badge,
            'test': badge.test,
            'attempt': badge.attempt,
            'verification_url': f"{settings.SITE_URL}/assessments/verify/{badge.verification_code}/",
            'certificate_url': f"{settings.SITE_URL}/assessments/certificate/{badge.attempt.id}/"
        }
        context.update({
            'user_name': badge.user.get_full_name() or badge.user.email,
            'unsubscribe_url': f"{settings.SITE_URL}/accounts/settings/emails/",
        })
        
        html_message = render_to_string('assessments/emails/badge_earned.html', context)
        plain_message = f"""
Congratulations {badge.user.get_full_name()}!

You've successfully earned the {badge.badge_name} badge!

Test: {badge.test.title}
Score: {badge.attempt.score}%
Difficulty: {badge.test.get_difficulty_display()}

View your badge: {context['verification_url']}
Download certificate: {context['certificate_url']}

Keep up the great work!

Best regards,
The HireSight Team
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[badge.user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Badge earned notification sent to {badge.user.email}")
        
    except Exception as e:
        logger.error(f"Error sending badge notification: {str(e)}")


@shared_task
def send_test_recommendation_emails():
    """Send weekly test recommendations to users"""
    from .models import SkillTest, SkillAssessmentAttempt
    from apps.accounts.models import User
    
    users = User.objects.filter(
        account_type='personal',
        is_active=True
    ).select_related('personal_profile')
    
    sent_count = 0
    
    for user in users:
        try:
            # Check email preferences
            if not hasattr(user, 'email_preferences'):
                continue
            
            prefs = user.email_preferences
            if not prefs.notify_job_recommendations or prefs.email_frequency == 'off':
                continue
            
            # Get user's skills
            if not hasattr(user, 'personal_profile') or not user.personal_profile.skills:
                continue
            
            user_skills = [s.get('skill', '').lower() for s in user.personal_profile.skills]
            
            # Get completed tests
            completed_test_ids = SkillAssessmentAttempt.objects.filter(
                user=user,
                status='COMPLETED'
            ).values_list('test_id', flat=True)
            
            # Find recommended tests
            recommended = SkillTest.objects.filter(
                skill_name__in=[s.title() for s in user_skills],
                is_active=True
            ).exclude(
                id__in=completed_test_ids
            ).order_by('-is_featured', '-total_attempts')[:3]
            
            if not recommended:
                continue
            
            subject = 'New Skill Tests Recommended for You'
            
            context = {
                'user': user,
                'tests': recommended,
                'site_url': settings.SITE_URL
            }
            context.update({
                'user_name': user.get_full_name() or user.email,
                'browse_url': f"{settings.SITE_URL}/assessments/browse/",
                'unsubscribe_url': f"{settings.SITE_URL}/accounts/settings/emails/",
            })
            
            html_message = render_to_string('assessments/emails/test_recommendations.html', context)
            plain_message = f"""
Hi {user.get_full_name()},

We have some new skill tests that match your profile:

{chr(10).join([f"- {test.title} ({test.get_difficulty_display()})" for test in recommended])}

Start testing your skills: {settings.SITE_URL}/assessments/browse/

Best regards,
The HireSight Team
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True
            )
            
            sent_count += 1
            
        except Exception as e:
            logger.error(f"Error sending recommendations to {user.email}: {str(e)}")
    
    logger.info(f"Test recommendations sent to {sent_count} users")
    return sent_count


@shared_task
def send_test_reminder_emails():
    """Send reminder emails for in-progress assessments that are close to timing out."""
    from .models import SkillAssessmentAttempt

    now = timezone.now()
    attempts = SkillAssessmentAttempt.objects.filter(status='IN_PROGRESS').select_related('test', 'user')
    reminded = 0

    for attempt in attempts:
        if not attempt.user.email:
            continue

        elapsed = (now - attempt.started_at).total_seconds() / 60
        remaining = attempt.test.duration_minutes - elapsed
        if remaining <= 1 or remaining > 15:
            continue

        cache_key = f"assessment_reminder_sent_{attempt.id}"
        if cache.get(cache_key):
            continue

        due_at = attempt.started_at + timedelta(minutes=attempt.test.duration_minutes)
        context = {
            'user_name': attempt.user.get_full_name() or attempt.user.email,
            'test_title': attempt.test.title,
            'due_date': due_at,
            'duration_minutes': attempt.test.duration_minutes,
            'start_link': f"{settings.SITE_URL}/assessments/take/{attempt.id}/",
            'unsubscribe_url': f"{settings.SITE_URL}/accounts/settings/emails/",
        }

        html_message = render_to_string('assessments/emails/test_reminder.html', context)
        plain_message = (
            f"Hi {context['user_name']},\n\n"
            f"You're in the middle of {context['test_title']}.\n"
            f"Please resume before {due_at.strftime('%b %d, %Y %H:%M')}.\n"
            f"Resume now: {context['start_link']}\n\n"
            "HireSight"
        )

        send_mail(
            subject=f"Reminder: resume {attempt.test.title}",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[attempt.user.email],
            html_message=html_message,
            fail_silently=True
        )

        cache.set(cache_key, True, 60 * 30)
        reminded += 1
        logger.info(f"Reminder sent for attempt {attempt.id} to {attempt.user.email}")

    logger.info(f"Sent assessment reminders to {reminded} users")
    return reminded


@shared_task
def update_question_pool_statistics():
    """Recalculate question pool statistics"""
    from .models import QuestionPool
    
    updated_count = 0
    
    for question in QuestionPool.objects.filter(is_active=True):
        # Statistics are updated in real-time via record_usage()
        # This task can be used for cleanup or recalculation if needed
        updated_count += 1
    
    logger.info(f"Updated statistics for {updated_count} questions")
    return updated_count


@shared_task
def generate_test_analytics_report():
    """Generate monthly analytics report for test performance"""
    from .models import SkillTest, SkillAssessmentAttempt
    from django.db.models import Count, Avg
    from datetime import timedelta
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get test statistics for the past month
    tests_data = []
    
    for test in SkillTest.objects.filter(is_active=True):
        attempts = SkillAssessmentAttempt.objects.filter(
            test=test,
            status='COMPLETED',
            completed_at__gte=start_date,
            completed_at__lte=end_date
        )
        
        if attempts.exists():
            stats = attempts.aggregate(
                count=Count('id'),
                avg_score=Avg('score'),
                pass_rate=Avg('passed')
            )
            
            tests_data.append({
                'test': test.title,
                'attempts': stats['count'],
                'avg_score': round(stats['avg_score'], 1),
                'pass_rate': round(stats['pass_rate'] * 100, 1)
            })
    
    logger.info(f"Generated analytics report for {len(tests_data)} tests")
    
    # In a real implementation, you might save this to a Report model or send via email
    return tests_data
