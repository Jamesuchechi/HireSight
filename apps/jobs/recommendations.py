"""
Job recommendation system for HireSight.

This module provides AI-powered job recommendations by combining:
1. Skills and experience matching
2. User preferences (job types, remote work, salary)
3. Location preferences
4. Collaborative filtering based on user behavior
5. Job interaction history (saved, viewed, applied)
"""

import math
from typing import List, Dict, Tuple, Optional
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import Job, SavedJob, JobView
from apps.applications.models import Application
from apps.accounts.models import PersonalProfile


class JobRecommendationEngine:
    """Engine for calculating job-user match scores and recommendations."""

    def __init__(self):
        self.weights = {
            'skills_match': 0.35,
            'experience_match': 0.20,
            'preferences_match': 0.15,
            'location_match': 0.10,
            'collaborative_score': 0.15,
            'recency_bonus': 0.05,
        }

    def calculate_match_score(self, user, job) -> float:
        """
        Calculate overall match score between a user and job (0.0 to 1.0).

        Combines multiple factors:
        - Skills matching
        - Experience level compatibility
        - User preferences alignment
        - Location compatibility
        - Collaborative filtering score
        - Recency bonus for new jobs
        """
        if not hasattr(user, 'personal_profile'):
            return 0.0

        profile = user.personal_profile

        # Calculate individual component scores
        skills_score = self._calculate_skills_match(profile, job)
        experience_score = self._calculate_experience_match(profile, job)
        preferences_score = self._calculate_preferences_match(profile, job)
        location_score = self._calculate_location_match(profile, job)
        collaborative_score = self._calculate_collaborative_score(user, job)
        recency_score = self._calculate_recency_bonus(job)

        # Weighted combination
        total_score = (
            skills_score * self.weights['skills_match'] +
            experience_score * self.weights['experience_match'] +
            preferences_score * self.weights['preferences_match'] +
            location_score * self.weights['location_match'] +
            collaborative_score * self.weights['collaborative_score'] +
            recency_score * self.weights['recency_bonus']
        )

        return min(total_score, 1.0)  # Cap at 1.0

    def _calculate_skills_match(self, profile: PersonalProfile, job: Job) -> float:
        """Calculate skills match score (0.0 to 1.0)."""
        if not profile.skills or not job.requirements:
            return 0.0

        user_skills = {skill.get('skill', '').lower() for skill in profile.skills}
        job_skills = set()

        # Extract skills from job requirements
        requirements = job.requirements
        if isinstance(requirements, dict):
            for key, value in requirements.items():
                if isinstance(value, list):
                    job_skills.update(skill.lower() for skill in value if isinstance(skill, str))
                elif isinstance(value, str):
                    job_skills.add(value.lower())

        if not job_skills:
            return 0.5  # Neutral score if no specific skills required

        # Calculate Jaccard similarity
        intersection = len(user_skills & job_skills)
        union = len(user_skills | job_skills)

        if union == 0:
            return 0.0

        return intersection / union

    def _calculate_experience_match(self, profile: PersonalProfile, job: Job) -> float:
        """Calculate experience level compatibility (0.0 to 1.0)."""
        if not profile.experience:
            return 0.3  # Low score for no experience

        # Count years of experience
        total_years = 0
        for exp in profile.experience:
            if isinstance(exp, dict) and 'start_date' in exp and 'end_date' in exp:
                # Simple year calculation (could be improved)
                total_years += 1  # Rough estimate

        # Map experience level to year ranges
        level_ranges = {
            'entry': (0, 2),
            'mid': (2, 5),
            'senior': (5, 10),
            'lead': (8, 15),
            'executive': (10, 20),
        }

        job_level = job.experience_level
        if job_level not in level_ranges:
            return 0.5

        min_years, max_years = level_ranges[job_level]

        if total_years < min_years:
            return max(0.0, total_years / min_years * 0.7)  # Partial credit
        elif total_years <= max_years:
            return 1.0  # Perfect match
        else:
            # Too experienced, but still good match
            return max(0.6, 1.0 - (total_years - max_years) * 0.1)

    def _calculate_preferences_match(self, profile: PersonalProfile, job: Job) -> float:
        """Calculate user preferences match score (0.0 to 1.0)."""
        score = 0.0
        factors = 0

        # Employment type preference
        if profile.preferred_job_types:
            factors += 1
            if job.employment_type in profile.preferred_job_types:
                score += 1.0
            else:
                score += 0.3  # Partial credit for flexibility

        # Remote work preference
        factors += 1
        if profile.remote_preference == 'no_preference':
            score += 1.0
        elif profile.remote_preference == 'remote' and job.is_remote:
            score += 1.0
        elif profile.remote_preference == 'on-site' and not job.is_remote:
            score += 1.0
        elif profile.remote_preference == 'hybrid' and job.remote_type == 'hybrid':
            score += 1.0
        else:
            score += 0.2  # Some flexibility

        # Salary expectations
        if profile.salary_expectation_min and job.salary_max:
            factors += 1
            salary_min_value = float(profile.salary_expectation_min)
            salary_max_value = float(job.salary_max)
            expected_max = float(profile.salary_expectation_max or job.salary_max)
            if salary_min_value <= salary_max_value:
                overlap_ratio = min(salary_max_value, expected_max) / salary_max_value if salary_max_value else 0
                score += max(0.3, overlap_ratio)
            else:
                score += 0.1  # Significant mismatch

        return score / max(factors, 1)

    def _calculate_location_match(self, profile: PersonalProfile, job: Job) -> float:
        """Calculate location compatibility (0.0 to 1.0)."""
        if not profile.location or job.is_remote:
            return 1.0  # Remote jobs or no location preference = perfect match

        # Simple text-based matching (could be improved with geocoding)
        user_location = profile.location.lower()
        job_location = job.location.lower()

        if user_location in job_location or job_location in user_location:
            return 1.0

        # Check for same city/state/country
        user_parts = set(user_location.split())
        job_parts = set(job_location.split())

        if user_parts & job_parts:  # Any common location components
            return 0.8

        return 0.3  # Different locations but still possible

    def _calculate_collaborative_score(self, user, job: Job) -> float:
        """Calculate collaborative filtering score based on similar users (0.0 to 1.0)."""
        # Find users who have interacted with this job
        interacted_users = set()

        # Users who saved this job
        saved_users = SavedJob.objects.filter(job=job).values_list('user', flat=True)
        interacted_users.update(saved_users)

        # Users who applied to this job
        applied_users = Application.objects.filter(job=job).values_list('applicant', flat=True)
        interacted_users.update(applied_users)

        # Users who viewed this job recently
        recent_views = JobView.objects.filter(
            job=job,
            viewed_at__gte=timezone.now() - timedelta(days=30)
        ).values_list('user', flat=True)
        interacted_users.update(recent_views)

        if not interacted_users:
            return 0.5  # Neutral score

        # Calculate similarity based on shared interactions
        similar_users = self._find_similar_users(user, interacted_users)
        if similar_users:
            return 0.8  # High score if similar users interacted

        return 0.4  # Moderate score for general popularity

    def _find_similar_users(self, user, candidate_users: set) -> List:
        """Find users with similar interaction patterns."""
        # Get user's interaction history
        user_saved = set(SavedJob.objects.filter(user=user).values_list('job', flat=True))
        user_applied = set(Application.objects.filter(applicant=user).values_list('job', flat=True))
        user_viewed = set(JobView.objects.filter(user=user).values_list('job', flat=True))

        user_interactions = user_saved | user_applied | user_viewed

        similar_users = []
        for candidate_id in candidate_users:
            if candidate_id == user.id:
                continue

            # Check shared interactions
            candidate_saved = set(SavedJob.objects.filter(user=candidate_id).values_list('job', flat=True))
            candidate_applied = set(Application.objects.filter(applicant=candidate_id).values_list('job', flat=True))
            candidate_viewed = set(JobView.objects.filter(user=candidate_id).values_list('job', flat=True))

            candidate_interactions = candidate_saved | candidate_applied | candidate_viewed

            # Calculate Jaccard similarity of interactions
            intersection = len(user_interactions & candidate_interactions)
            union = len(user_interactions | candidate_interactions)

            if union > 0 and (intersection / union) > 0.3:  # 30% similarity threshold
                similar_users.append(candidate_id)

        return similar_users

    def _calculate_recency_bonus(self, job: Job) -> float:
        """Calculate recency bonus for new jobs (0.0 to 1.0)."""
        days_since_published = (timezone.now() - job.published_at).days if job.published_at else 30

        if days_since_published <= 1:
            return 1.0  # Very new job
        elif days_since_published <= 7:
            return 0.7  # New this week
        elif days_since_published <= 30:
            return 0.4  # New this month
        else:
            return 0.1  # Older job

    def get_recommendations_for_user(self, user, limit: int = 20) -> List[Tuple[Job, float]]:
        """
        Get personalized job recommendations for a user.

        Returns list of (job, score) tuples sorted by score descending.
        """
        if not hasattr(user, 'personal_profile'):
            return []

        # Get active jobs not already interacted with
        interacted_job_ids = set()

        # Jobs user has saved
        interacted_job_ids.update(SavedJob.objects.filter(user=user).values_list('job_id', flat=True))

        # Jobs user has applied to
        interacted_job_ids.update(Application.objects.filter(applicant=user).values_list('job_id', flat=True))

        # Get recent job views (exclude very old views)
        recent_views = JobView.objects.filter(
            user=user,
            viewed_at__gte=timezone.now() - timedelta(days=90)
        ).values_list('job_id', flat=True)
        interacted_job_ids.update(recent_views)

        # Get candidate jobs
        candidate_jobs = Job.objects.filter(
            status='active'
        ).exclude(
            id__in=interacted_job_ids
        )[:limit * 3]  # Get more candidates for scoring

        # Calculate scores
        scored_jobs = []
        for job in candidate_jobs:
            score = self.calculate_match_score(user, job)
            scored_jobs.append((job, score))

        # Sort by score descending and return top results
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        return scored_jobs[:limit]

    def get_similar_jobs(self, job: Job, limit: int = 10) -> List[Tuple[Job, float]]:
        """
        Find jobs similar to the given job.

        Used for "similar jobs" recommendations.
        """
        # Simple similarity based on shared requirements and attributes
        similar_jobs = []

        # Find jobs with similar skills
        job_skills = set()
        if job.requirements:
            for key, value in job.requirements.items():
                if isinstance(value, list):
                    job_skills.update(str(skill).lower() for skill in value)

        candidate_jobs = Job.objects.filter(
            status='active'
        ).exclude(id=job.id)

        for candidate in candidate_jobs:
            similarity_score = 0.0
            factors = 0

            # Skills similarity
            candidate_skills = set()
            if candidate.requirements:
                for key, value in candidate.requirements.items():
                    if isinstance(value, list):
                        candidate_skills.update(str(skill).lower() for skill in value)

            if job_skills and candidate_skills:
                intersection = len(job_skills & candidate_skills)
                union = len(job_skills | candidate_skills)
                if union > 0:
                    similarity_score += (intersection / union) * 0.5
                    factors += 1

            # Employment type match
            if candidate.employment_type == job.employment_type:
                similarity_score += 0.2
                factors += 1

            # Experience level match
            if candidate.experience_level == job.experience_level:
                similarity_score += 0.2
                factors += 1

            # Remote type match
            if candidate.remote_type == job.remote_type:
                similarity_score += 0.1
                factors += 1

            if factors > 0:
                final_score = similarity_score / factors
                similar_jobs.append((candidate, final_score))

        # Sort by similarity score
        similar_jobs.sort(key=lambda x: x[1], reverse=True)
        return similar_jobs[:limit]


# Global instance for easy access
recommendation_engine = JobRecommendationEngine()
