"""
Advanced filtering and search for jobs.
"""

from django.db.models import Q, Count, Case, When, IntegerField
from datetime import timedelta
from django.utils import timezone


class JobFilter:
    """Advanced job filtering and search."""

    def __init__(self, queryset, params):
        """
        Initialize filter with queryset and filter parameters.
        
        Args:
            queryset: Base Job queryset
            params: Dictionary of filter parameters
        """
        self.queryset = queryset
        self.params = params

    def filter(self):
        """Apply all filters and return filtered queryset."""
        qs = self.queryset

        # Search
        search = self.params.get('search', '').strip()
        if search:
            qs = self._filter_search(qs, search)

        # Location
        location = self.params.get('location', '').strip()
        if location:
            qs = qs.filter(location__icontains=location)

        # Remote type
        remote_type = self.params.get('remote_type')
        if remote_type:
            qs = qs.filter(remote_type=remote_type)

        # Employment type
        employment_type = self.params.get('employment_type')
        if employment_type:
            qs = qs.filter(employment_type=employment_type)

        # Experience level
        experience_level = self.params.get('experience_level')
        if experience_level:
            qs = qs.filter(experience_level=experience_level)

        # Salary
        salary_min = self.params.get('salary_min')
        if salary_min:
            try:
                qs = qs.filter(salary_min__gte=float(salary_min))
            except (ValueError, TypeError):
                pass

        # Posted within
        posted_within = self.params.get('posted_within')
        if posted_within:
            qs = self._filter_posted_within(qs, posted_within)

        # Remote only
        remote_only = self.params.get('remote_only')
        if remote_only:
            qs = qs.filter(is_remote=True)

        # Has salary
        has_salary = self.params.get('has_salary')
        if has_salary:
            qs = qs.filter(salary_min__isnull=False)

        # Sorting
        sort_by = self.params.get('sort_by', 'relevance')
        qs = self._apply_sorting(qs, sort_by, search)

        return qs

    def _filter_search(self, queryset, search):
        """
        Apply search filter across multiple fields.
        
        Searches in:
        - Job title
        - Job description
        - Company name
        - Location
        """
        return queryset.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(responsibilities__icontains=search) |
            Q(company__company_name__icontains=search) |
            Q(location__icontains=search)
        )

    def _filter_posted_within(self, queryset, days):
        """Filter jobs posted within N days."""
        try:
            days_int = int(days)
            cutoff_date = timezone.now() - timedelta(days=days_int)
            return queryset.filter(published_at__gte=cutoff_date)
        except (ValueError, TypeError):
            return queryset

    def _apply_sorting(self, queryset, sort_by, search_term=None):
        """
        Apply sorting to queryset.
        
        Sort options:
        - relevance: Sort by search relevance (if search term provided)
        - date: Most recent first
        - salary: Highest salary first
        """
        if sort_by == 'date':
            return queryset.order_by('-published_at', '-created_at')
        
        elif sort_by == 'salary':
            return queryset.order_by('-salary_max', '-salary_min', '-published_at')
        
        elif sort_by == 'relevance' and search_term:
            # Annotate with relevance score
            return self._sort_by_relevance(queryset, search_term)
        
        # Default: recent first
        return queryset.order_by('-published_at', '-created_at')

    def _sort_by_relevance(self, queryset, search_term):
        """
        Sort by relevance to search term.
        
        Scoring:
        - Title match: 10 points
        - Company match: 5 points
        - Description match: 2 points
        - Location match: 1 point
        """
        search_lower = search_term.lower()
        
        queryset = queryset.annotate(
            relevance_score=Case(
                # Title contains search
                When(title__icontains=search_lower, then=10),
                default=0,
                output_field=IntegerField(),
            ) + Case(
                # Company name contains search
                When(company__company_name__icontains=search_lower, then=5),
                default=0,
                output_field=IntegerField(),
            ) + Case(
                # Description contains search
                When(description__icontains=search_lower, then=2),
                default=0,
                output_field=IntegerField(),
            ) + Case(
                # Location contains search
                When(location__icontains=search_lower, then=1),
                default=0,
                output_field=IntegerField(),
            )
        )
        
        return queryset.order_by('-relevance_score', '-published_at')


class JobRecommender:
    """Recommend jobs based on user profile."""

    def __init__(self, user):
        """
        Initialize recommender for user.
        
        Args:
            user: User object with personal profile
        """
        self.user = user
        self.profile = getattr(user, 'personal_profile', None)

    def get_recommendations(self, limit=10):
        """
        Get recommended jobs for user.
        
        Args:
            limit: Maximum number of recommendations
            
        Returns:
            Queryset of recommended jobs
        """
        from .models import Job, JobStatus
        
        # Start with active jobs
        queryset = Job.objects.filter(status=JobStatus.ACTIVE)
        
        if not self.profile:
            # No profile, return recent jobs
            return queryset.order_by('-published_at')[:limit]
        
        # Get user's skills
        user_skills = self.profile.skills or []
        
        if not user_skills:
            # No skills, return recent jobs
            return queryset.order_by('-published_at')[:limit]
        
        # Filter by skills match
        # This is a simple implementation - in production, you'd use
        # more sophisticated matching algorithms
        q_objects = Q()
        for skill in user_skills:
            q_objects |= Q(requirements__icontains=skill)
        
        queryset = queryset.filter(q_objects)
        
        # Filter by experience level if available
        if hasattr(self.profile, 'experience_years') and self.profile.experience_years:
            years = self.profile.experience_years
            
            if years < 2:
                queryset = queryset.filter(experience_level='entry')
            elif years < 5:
                queryset = queryset.filter(experience_level__in=['entry', 'mid'])
            elif years < 10:
                queryset = queryset.filter(experience_level__in=['mid', 'senior'])
            else:
                queryset = queryset.filter(experience_level__in=['senior', 'lead', 'executive'])
        
        # Filter by location preference if available
        if hasattr(self.profile, 'preferred_locations') and self.profile.preferred_locations:
            locations = self.profile.preferred_locations
            location_q = Q()
            for loc in locations:
                location_q |= Q(location__icontains=loc)
            queryset = queryset.filter(location_q | Q(is_remote=True))
        
        # Filter by salary expectation if available
        if hasattr(self.profile, 'salary_expectation_min') and self.profile.salary_expectation_min:
            queryset = queryset.filter(
                salary_min__gte=self.profile.salary_expectation_min
            )
        
        # Order by most recent
        return queryset.order_by('-published_at')[:limit]


def get_similar_jobs(job, limit=5):
    """
    Get jobs similar to the given job.
    
    Args:
        job: Job object
        limit: Maximum number of similar jobs
        
    Returns:
        Queryset of similar jobs
    """
    from .models import Job, JobStatus
    
    # Find jobs with same:
    # 1. Employment type
    # 2. Experience level
    # 3. Location or remote type
    # 4. Exclude current job
    
    similar = Job.objects.filter(
        status=JobStatus.ACTIVE
    ).exclude(
        pk=job.pk
    )
    
    # Same employment type
    similar = similar.filter(employment_type=job.employment_type)
    
    # Same or adjacent experience level
    experience_groups = {
        'entry': ['entry', 'mid'],
        'mid': ['entry', 'mid', 'senior'],
        'senior': ['mid', 'senior', 'lead'],
        'lead': ['senior', 'lead', 'executive'],
        'executive': ['lead', 'executive'],
    }
    
    adjacent_levels = experience_groups.get(job.experience_level, [job.experience_level])
    similar = similar.filter(experience_level__in=adjacent_levels)
    
    # Same location or both remote
    if job.is_remote:
        similar = similar.filter(is_remote=True)
    else:
        similar = similar.filter(
            Q(location__icontains=job.location) |
            Q(is_remote=True)
        )
    
    # Order by most recent
    return similar.order_by('-published_at')[:limit]