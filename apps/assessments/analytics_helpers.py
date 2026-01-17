"""
Helpers for integrating the assessment system with analytics tooling.
"""
import logging
from datetime import timedelta

from django.db.models import Avg, Count, Q, Max, Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.applications.models import Application
from apps.assessments.models import SkillAssessmentAttempt, SkillBadge

logger = logging.getLogger(__name__)


def track_assessment_completion(attempt):
    """Send assessment completion events to analytics."""
    try:
        from apps.analytics.models import UserEvent

        UserEvent.objects.create(
            user=attempt.user,
            event_type='assessment_completed',
            event_data={
                'test_id': str(attempt.test.id),
                'test_title': attempt.test.title,
                'skill_name': attempt.test.skill_name,
                'difficulty': attempt.test.difficulty,
                'score': attempt.score,
                'passed': attempt.passed,
                'time_taken': attempt.time_taken_minutes,
                'questions_count': len(attempt.frozen_questions),
            },
            timestamp=attempt.completed_at or timezone.now()
        )
    except ImportError:
        logger.debug('Analytics UserEvent model unavailable for tracking.')


def track_badge_earned(badge):
    """Send badge earned events to analytics."""
    try:
        from apps.analytics.models import UserEvent

        UserEvent.objects.create(
            user=badge.user,
            event_type='badge_earned',
            event_data={
                'badge_id': str(badge.id),
                'badge_name': badge.badge_name,
                'skill_name': badge.test.skill_name,
                'difficulty': badge.badge_level,
                'score': badge.attempt.score,
            },
            timestamp=badge.issued_at
        )
    except ImportError:
        logger.debug('Analytics UserEvent model unavailable for badge tracking.')


def _get_proficiency_level(score):
    """Translate score to human-friendly proficiency level."""
    if score >= 90:
        return 'Expert'
    if score >= 75:
        return 'Advanced'
    if score >= 60:
        return 'Intermediate'
    return 'Beginner'


def get_skill_proficiency_data(user):
    """Fetch user's proficiency metrics per skill."""
    skills = SkillAssessmentAttempt.objects.filter(
        user=user,
        status='COMPLETED'
    ).values('test__skill_name').annotate(
        best_score=Avg('score'),
        attempts_count=Count('id'),
        passed_count=Count('id', filter=Q(passed=True)),
        last_completed=Max('completed_at')
    ).order_by('-best_score')

    proficiency = []
    for entry in skills:
        score = entry.get('best_score') or 0
        proficiency.append({
            'skill': entry['test__skill_name'],
            'score': round(score, 1),
            'attempts': entry.get('attempts_count', 0),
            'passed': entry.get('passed_count', 0),
            'level': _get_proficiency_level(score),
            'last_completed': entry.get('last_completed')
        })

    return proficiency


def get_assessment_trends(user, days=30):
    """Return recent scores per assessment for trend charts."""
    cutoff = timezone.now() - timedelta(days=days)
    attempts = SkillAssessmentAttempt.objects.filter(
        user=user,
        status='COMPLETED',
        completed_at__gte=cutoff
    ).order_by('completed_at')

    trends = []
    for attempt in attempts:
        trends.append({
            'date': attempt.completed_at.strftime('%Y-%m-%d'),
            'score': attempt.score,
            'skill': attempt.test.skill_name,
            'passed': attempt.passed,
            'time_taken': attempt.time_taken_minutes or 0,
        })
    return trends


def generate_assessment_report_for_user(user):
    """Aggregate assessment stats for a single user."""
    attempts = SkillAssessmentAttempt.objects.filter(user=user, status='COMPLETED')
    total_attempts = attempts.count()
    if total_attempts == 0:
        return None

    passed_attempts = attempts.filter(passed=True).count()
    avg_score = attempts.aggregate(avg=Avg('score'))['avg'] or 0
    total_time_spent = attempts.aggregate(total=Sum('time_taken_minutes'))['total'] or 0

    report = {
        'total_attempts': total_attempts,
        'total_passed': passed_attempts,
        'pass_rate': round((passed_attempts / total_attempts) * 100, 1),
        'total_badges': SkillBadge.objects.filter(user=user).count(),
        'average_score': round(avg_score, 1),
        'total_time_spent': round(total_time_spent or 0, 1),
        'skills_tested': attempts.values('test__skill_name').distinct().count(),
        'recent_activity': [
            {
                'test': attempt.test.title,
                'skill': attempt.test.skill_name,
                'score': attempt.score,
                'completed_at': attempt.completed_at.strftime('%Y-%m-%d') if attempt.completed_at else None,
                'passed': attempt.passed,
            }
            for attempt in attempts.order_by('-completed_at')[:5]
        ],
        'top_skills': get_skill_proficiency_data(user)[:5],
    }

    return report


def get_company_candidate_insights(company_profile):
    """Provide companies with insights about candidates with badges."""
    applicants_with_badges = Application.objects.filter(
        job__company=company_profile,
        applicant__skill_badges__isnull=False
    ).values('applicant').distinct()

    skill_distribution = SkillBadge.objects.filter(
        user__job_applications__job__company=company_profile
    ).values('test__skill_name').annotate(
        count=Count('id'),
        avg_score=Avg('attempt__score')
    ).order_by('-count')

    return {
        'total_candidates_with_badges': applicants_with_badges.count(),
        'skill_distribution': list(skill_distribution),
        'top_skills': list(skill_distribution[:5]),
    }


@receiver(post_save, sender=SkillAssessmentAttempt)
def _track_assessment(sender, instance, created, **kwargs):
    if instance.status == 'COMPLETED' and instance.score is not None:
        track_assessment_completion(instance)


@receiver(post_save, sender=SkillBadge)
def _track_badge(sender, instance, created, **kwargs):
    if created:
        track_badge_earned(instance)
