import logging
from datetime import timedelta

from django.db import OperationalError
from django.db.models import Avg, Count, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Achievement, SkillAssessmentAttempt, UserAchievement

logger = logging.getLogger(__name__)

DEFAULT_ACHIEVEMENTS = [
    {
        'code': 'first_attempt_pass',
        'name': 'First Attempt Glory',
        'description': 'Pass an assessment on your very first attempt.',
        'icon': '🥇',
        'type': 'first_attempt_pass',
        'criteria': {}
    },
    {
        'code': 'perfect_score',
        'name': 'Perfect Score',
        'description': 'Score 100% on any assessment.',
        'icon': '💯',
        'type': 'perfect_score',
        'criteria': {}
    },
    {
        'code': 'speed_demon',
        'name': 'Speed Demon',
        'description': 'Finish an assessment in half the allotted time or less.',
        'icon': '⚡',
        'type': 'speed_demon',
        'criteria': {'threshold_ratio': 0.5}
    },
    {
        'code': 'consistency_king',
        'name': 'Consistency King',
        'description': 'Pass five consecutive assessments with 85%+.',
        'icon': '🏆',
        'type': 'consistency_king',
        'criteria': {'length': 5, 'score_threshold': 85}
    },
    {
        'code': 'skill_master',
        'name': 'Skill Master',
        'description': 'Score 90%+ on three attempts for the same skill.',
        'icon': '🧠',
        'type': 'skill_master',
        'criteria': {'attempts': 3, 'score_threshold': 90}
    },
]


def ensure_default_achievements():
    for data in DEFAULT_ACHIEVEMENTS:
        try:
            Achievement.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'icon': data['icon'],
                    'type': data['type'],
                    'criteria': data.get('criteria', {})
                }
            )
        except OperationalError:
            logger.debug('Achievement table not ready yet, skipping default creation.')


def award_achievement(user, code, metadata=None):
    achievement = Achievement.objects.filter(code=code).first()
    if not achievement:
        return False
    metadata = metadata or {}
    obj, created = UserAchievement.objects.get_or_create(
        user=user,
        achievement=achievement,
        defaults={'metadata': metadata}
    )
    if created:
        logger.info(f"Awarded achievement {code} to {user.email}")
    return created


@receiver(post_save, sender=SkillAssessmentAttempt)
def _evaluate_achievements(sender, instance, **kwargs):
    if instance.is_practice_mode or instance.status != 'COMPLETED' or instance.score is None:
        return

    user = instance.user
    metadata = {
        'score': instance.score,
        'skill': instance.test.skill_name,
        'attempt_id': str(instance.id)
    }

    # First attempt pass
    total_completed = SkillAssessmentAttempt.objects.filter(
        user=user,
        test=instance.test,
        status='COMPLETED'
    ).count()
    if total_completed == 1 and instance.passed:
        award_achievement(user, 'first_attempt_pass', metadata)

    if instance.score == 100:
        award_achievement(user, 'perfect_score', metadata)

    if instance.time_taken_minutes and instance.test.duration_minutes:
        if instance.time_taken_minutes <= (instance.test.duration_minutes * 0.5):
            award_achievement(user, 'speed_demon', metadata)

    recent_attempts = list(
        SkillAssessmentAttempt.objects.filter(
            user=user,
            status='COMPLETED'
        ).order_by('-completed_at')[:5]
    )
    if len(recent_attempts) >= 5 and all(
        att.passed and (att.score or 0) >= 85 for att in recent_attempts
    ):
        award_achievement(user, 'consistency_king', {
            **metadata,
            'recent_scores': [att.score for att in recent_attempts]
        })

    skill_attempts = SkillAssessmentAttempt.objects.filter(
        user=user,
        test__skill_name__iexact=instance.test.skill_name,
        status='COMPLETED'
    ).order_by('-completed_at')[:5]
    if len(skill_attempts) >= 3:
        scores = [att.score or 0 for att in skill_attempts[:3]]
        if len(scores) == 3 and sum(scores) / 3 >= 90 and all(att.passed for att in skill_attempts[:3]):
            award_achievement(user, 'skill_master', {
                **metadata,
                'skill': instance.test.skill_name,
                'scores': scores
            })
