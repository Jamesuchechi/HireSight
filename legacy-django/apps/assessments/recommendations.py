"""
Test recommendation utilities for HireSight assessments.
"""
from collections import Counter

from django.db.models import Q

from apps.applications.models import Application
from .models import SkillAssessmentAttempt, SkillTest


class TestRecommendationEngine:
    """Recommend tests based on profile skills, applications, and behavior."""

    def recommend_for_user(self, user, limit=5):
        profile_skills = self._get_profile_skills(user)
        job_skills = self._get_job_application_skills(user)
        partial_skills = self._get_partial_attempt_skills(user)

        candidates = []
        base_qs = SkillTest.objects.filter(is_active=True)
        for test in base_qs:
            if not self._matches_required_skills(test, profile_skills):
                continue
            score = self._score_test(test, profile_skills, job_skills, partial_skills)
            candidates.append((score, test))

        candidates.sort(reverse=True, key=lambda pair: pair[0])
        return [test for score, test in candidates[:limit]]

    def _score_test(self, test, profile_skills, job_skills, partial_skills):
        weight = 0
        skill_lower = test.skill_name.lower()

        if skill_lower in profile_skills:
            weight += 35
        if skill_lower in job_skills:
            weight += 25
        if skill_lower in partial_skills:
            weight += 20

        weight += min(test.total_attempts / 100, 10)
        weight += (100 - len(test.required_skills or [])) if test.required_skills else 5
        return weight

    def _get_profile_skills(self, user):
        skills = set()
        profile = getattr(user, 'personal_profile', None)
        if not profile or not getattr(profile, 'skills', None):
            return skills
        for entry in profile.skills:
            name = entry.get('skill')
            if name:
                skills.add(name.lower())
        return skills

    def _get_job_application_skills(self, user):
        skills = Counter()
        applications = Application.objects.filter(applicant=user).select_related('job')
        for application in applications:
            job = application.job
            requirements = getattr(job, 'get_requirements_list', lambda: [])()
            for skill in requirements:
                if skill:
                    skills[skill.lower()] += 1
        return set(skills.keys())

    def _get_partial_attempt_skills(self, user):
        attempts = SkillAssessmentAttempt.objects.filter(
            user=user,
        ).exclude(status='COMPLETED').select_related('test')
        return {attempt.test.skill_name.lower() for attempt in attempts if attempt.test}

    def _matches_required_skills(self, test, profile_skills):
        if not test.required_skills:
            return True
        required = {skill.lower() for skill in test.required_skills if isinstance(skill, str)}
        if not required:
            return True
        return bool(required & profile_skills)
