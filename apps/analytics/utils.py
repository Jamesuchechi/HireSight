"""
Utility functions for analytics tracking and calculations.
"""
from collections import Counter
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
from .models import (
    ProfileView, JobView, SearchQuery,
    UserActivityLog, CompanyAnalyticsSnapshot,
    PersonalAnalyticsSnapshot
)


def track_profile_view(profile_owner, viewer=None, ip_address=None):
    """
    Track a profile view.
    
    Args:
        profile_owner: User whose profile is being viewed
        viewer: User viewing the profile (can be None for anonymous)
        ip_address: IP address of the viewer
    """
    ProfileView.objects.create(
        profile_owner=profile_owner,
        viewer=viewer,
        viewer_ip=ip_address
    )


def track_job_view(job, viewer=None, ip_address=None, referrer=None):
    """
    Track a job listing view.
    
    Args:
        job: Job being viewed
        viewer: User viewing the job (can be None for anonymous)
        ip_address: IP address of the viewer
        referrer: URL the viewer came from
    """
    JobView.objects.create(
        job=job,
        viewer=viewer,
        viewer_ip=ip_address,
        referrer=referrer
    )


def track_search_query(query_text, filters=None, results_count=0, user=None):
    """
    Track a search query.
    
    Args:
        query_text: The search query text
        filters: Dictionary of applied filters
        results_count: Number of results returned
        user: User performing the search (can be None for anonymous)
    """
    SearchQuery.objects.create(
        user=user,
        query_text=query_text,
        filters=filters or {},
        results_count=results_count
    )


def log_user_activity(user, action_type, metadata=None):
    """
    Log a user activity.
    
    Args:
        user: User performing the action
        action_type: Type of action (must be in UserActivityLog.ACTION_TYPES)
        metadata: Additional data about the action
    """
    UserActivityLog.objects.create(
        user=user,
        action_type=action_type,
        metadata=metadata or {}
    )


def get_client_ip(request):
    """
    Get the client's IP address from the request.
    
    Args:
        request: Django request object
        
    Returns:
        str: IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def calculate_application_success_rate(user):
    """
    Calculate the success rate for a user's applications.
    
    Args:
        user: User to calculate success rate for
        
    Returns:
        float: Success rate as a percentage
    """
    try:
        from apps.applications.models import Application
        
        total = Application.objects.filter(user=user).count()
        if total == 0:
            return 0.0
        
        successful = Application.objects.filter(
            user=user,
            status__in=['offer', 'hired']
        ).count()
        
        return (successful / total) * 100
    except ImportError:
        return 0.0


def calculate_time_to_hire(company):
    """
    Calculate average time to hire for a company.
    
    Args:
        company: Company user to calculate for
        
    Returns:
        float: Average days to hire, or None if no hires
    """
    try:
        from apps.applications.models import Application
        from django.db.models import Avg, F, ExpressionWrapper, DurationField
        
        hired = Application.objects.filter(
            job__company=company,
            status='hired',
            hired_at__isnull=False
        ).annotate(
            time_to_hire=ExpressionWrapper(
                F('hired_at') - F('applied_at'),
                output_field=DurationField()
            )
        )
        
        avg_duration = hired.aggregate(avg=Avg('time_to_hire'))['avg']
        
        if avg_duration:
            return avg_duration.days
        return None
    except ImportError:
        return None


def _extract_skill_matches(application):
    """Return matched skills from an application match details."""
    details = getattr(application, 'match_details', None) or {}
    skills_match = details.get('skills_match', {})
    matched = skills_match.get('matched', [])
    if isinstance(matched, list):
        return matched

    explanation = getattr(application, 'match_explanation', None)
    if explanation and isinstance(explanation, dict):
        skills = explanation.get('skills', [])
        if isinstance(skills, list):
            return skills

    return []


def _extract_missing_skills(application):
    """Return missing skill hints from an application."""
    details = getattr(application, 'match_details', None) or {}
    skills_match = details.get('skills_match', {})
    missing = skills_match.get('missing', [])
    if isinstance(missing, list):
        return missing
    return []


def get_top_skills_from_applications(job):
    """
    Extract top skills from applications to a job.
    
    Args:
        job: Job to analyze
        
    Returns:
        list: List of (skill, count) tuples
    """
    try:
        from apps.applications.models import Application

        applications = Application.objects.filter(job=job)
        skill_counts = Counter()

        for app in applications:
            skill_counts.update(_extract_skill_matches(app))

        return skill_counts.most_common(10)
    except ImportError:
        return []


def generate_analytics_report(user, date_range='30d'):
    """
    Generate a comprehensive analytics report for a user.
    
    Args:
        user: User to generate report for
        date_range: Date range ('7d', '30d', '90d', 'all')
        
    Returns:
        dict: Analytics data
    """
    today = timezone.now().date()
    
    if date_range == '7d':
        start_date = today - timedelta(days=7)
    elif date_range == '30d':
        start_date = today - timedelta(days=30)
    elif date_range == '90d':
        start_date = today - timedelta(days=90)
    else:  # 'all'
        start_date = None
    
    report = {
        'user': user.email,
        'account_type': user.account_type,
        'date_range': date_range,
        'generated_at': timezone.now(),
    }
    
    if user.account_type == 'company':
        report.update(_generate_company_report(user, start_date))
    else:
        report.update(_generate_personal_report(user, start_date))
    
    return report


def _generate_company_report(company, start_date=None):
    """Generate company-specific analytics report."""
    from apps.jobs.models import Job
    from apps.applications.models import Application
    from django.db.models import Count, Avg
    
    jobs_query = Job.objects.filter(company=company)
    apps_query = Application.objects.filter(job__company=company)
    
    if start_date:
        jobs_query = jobs_query.filter(created_at__gte=start_date)
        apps_query = apps_query.filter(applied_at__gte=start_date)
    
    return {
        'total_jobs': jobs_query.count(),
        'active_jobs': jobs_query.filter(status='active').count(),
        'total_applications': apps_query.count(),
        'avg_match_score': apps_query.aggregate(avg=Avg('match_score'))['avg'] or 0,
        'total_hires': apps_query.filter(status='hired').count(),
        'avg_time_to_hire': calculate_time_to_hire(company),
    }


def _generate_personal_report(user, start_date=None):
    """Generate personal analytics report."""
    from apps.applications.models import Application
    
    apps_query = Application.objects.filter(user=user)
    
    if start_date:
        apps_query = apps_query.filter(applied_at__gte=start_date)
        profile_views = ProfileView.objects.filter(
            profile_owner=user,
            viewed_at__gte=start_date
        ).count()
    else:
        profile_views = ProfileView.objects.filter(
            profile_owner=user
        ).count()
    
    return {
        'total_applications': apps_query.count(),
        'success_rate': calculate_application_success_rate(user),
        'avg_match_score': apps_query.aggregate(avg=Avg('match_score'))['avg'] or 0,
        'profile_views': profile_views,
    }


def get_top_skills_for_company(company, limit=10):
    """Return aggregated skill matches for a company."""
    try:
        from apps.applications.models import Application
    except ImportError:
        return []

    skill_counts = Counter()
    applications = Application.objects.filter(job__company=company)
    for app in applications:
        skill_counts.update(_extract_skill_matches(app))

    return skill_counts.most_common(limit)


def get_skill_gap_insights_for_company(company, limit=5):
    """Return top missing skills observed across applications."""
    try:
        from apps.applications.models import Application
    except ImportError:
        return []

    gap_counts = Counter()
    applications = Application.objects.filter(job__company=company)
    for app in applications:
        gap_counts.update(_extract_missing_skills(app))

    return gap_counts.most_common(limit)


def get_industry_benchmarks(company, window_days=30):
    """
    Compute simple industry benchmarks for the given company.
    """
    try:
        from apps.accounts.models import CompanyProfile
    except ImportError:
        return {}

    profile = getattr(company, 'company_profile', None)
    industry = profile.industry if profile else ''
    if not industry:
        return {}

    start_date = timezone.now().date() - timedelta(days=window_days)
    snapshots = CompanyAnalyticsSnapshot.objects.filter(
        company__company_profile__industry=industry,
        date__gte=start_date
    )

    if not snapshots.exists():
        return {}

    averages = snapshots.aggregate(
        avg_applications=Avg('total_applications'),
        avg_hires=Avg('total_hires'),
        avg_time_to_hire=Avg('avg_time_to_hire')
    )

    return {
        'industry': industry,
        'avg_applications': averages['avg_applications'] or 0,
        'avg_hires': averages['avg_hires'] or 0,
        'avg_time_to_hire': averages['avg_time_to_hire'] or 0,
    }


def calculate_predictive_score(company):
    """
    Calculate a heuristic likelihood-to-hire score for a company.
    """
    try:
        from apps.applications.models import Application

        today = timezone.now().date()
        window_start = today - timedelta(days=30)
        applications = Application.objects.filter(
            job__company=company,
            applied_at__date__gte=window_start
        ).order_by('-applied_at')

        total_apps = applications.count()
        hires = applications.filter(status='hired').count()
        hiring_rate = (hires / total_apps) if total_apps > 0 else 0

        avg_match_score = applications.aggregate(avg=Avg('match_score'))['avg'] or 0
        avg_match_score = avg_match_score / 100  # normalize to 0-1

        snapshot = CompanyAnalyticsSnapshot.objects.filter(company=company).order_by('-date')
        followers_change = 0
        if snapshot.count() >= 2:
            latest = snapshot.all()[0]
            previous = snapshot.all()[1]
            followers_change = latest.followers_count - previous.followers_count

        followers_factor = min(max(followers_change / 10, 0), 1)
        likelihood = round(
            (hiring_rate * 0.5) +
            (avg_match_score * 0.3) +
            (followers_factor * 0.2),
            3
        )

        key_drivers = [
            {'label': 'Hiring rate', 'value': hiring_rate},
            {'label': 'Avg match score', 'value': avg_match_score},
            {'label': 'Follower growth', 'value': followers_factor},
        ]

        confidence = min(1.0, total_apps / 100) if total_apps > 0 else 0.2

        return {
            'likelihood_to_hire': likelihood * 100,
            'confidence': confidence * 100,
            'key_drivers': key_drivers,
            'notes': 'Based on recent applications and engagement trends.'
        }
    except ImportError:
        return {
            'likelihood_to_hire': None,
            'confidence': None,
            'key_drivers': [],
            'notes': 'Insufficient data'
        }
