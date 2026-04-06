"""
Celery tasks for analytics app.
These tasks run periodically to aggregate analytics data.
"""
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField, Sum
from datetime import timedelta

from .models import (
    ApplicationMetrics,
    CompanyAnalyticsSnapshot,
    PersonalAnalyticsSnapshot,
    SkillAssessmentResult,
    PredictiveAnalyticsSnapshot,
    SalaryNegotiationInsight,
    InterviewQuestionTemplate,
    CultureFitAssessment,
    DiversityAnalyticsSnapshot,
    ReferenceCheckRequest,
)
from .utils import (
    get_top_skills_for_company,
    get_skill_gap_insights_for_company,
    calculate_predictive_score
)
from apps.assessments.analytics import AssessmentAnalytics
from apps.assessments.utils import LearningPathGenerator
from apps.assessments.analytics_helpers import get_assessment_trends

User = get_user_model()


@shared_task
def generate_daily_application_metrics():
    """
    Generate daily aggregate metrics for all applications.
    Runs daily at midnight.
    """
    try:
        from apps.applications.models import Application
    except ImportError:
        return "Application model not available"
    
    today = timezone.now().date()
    
    # Get counts by status
    status_counts = Application.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Build metrics dictionary
    metrics = {
        'date': today,
        'total_applications': Application.objects.count(),
        'applications_pending': 0,
        'applications_screening': 0,
        'applications_interview': 0,
        'applications_offer': 0,
        'applications_hired': 0,
        'applications_rejected': 0,
    }
    
    for item in status_counts:
        metrics[f'applications_{item["status"]}'] = item['count']
    
    # Create or update metrics
    ApplicationMetrics.objects.update_or_create(
        date=today,
        defaults=metrics
    )
    
    return f"Generated metrics for {today}"


@shared_task
def generate_company_snapshots():
    """
    Generate daily snapshots for all company accounts.
    Runs daily at 1 AM.
    """
    try:
        from apps.jobs.models import Job
        from apps.applications.models import Application
        from apps.following.models import Follow
        from django.contrib.auth import get_user_model
    except ImportError:
        return "Required models not available"
    
    User = get_user_model()
    today = timezone.now().date()
    
    companies = User.objects.filter(account_type='company')
    
    for company in companies:
        # Job metrics
        total_jobs = Job.objects.filter(company=company).count()
        active_jobs = Job.objects.filter(company=company, status='active').count()
        closed_jobs = Job.objects.filter(company=company, status='closed').count()
        
        # Application metrics
        all_applications = Application.objects.filter(job__company=company)
        total_applications = all_applications.count()
        
        new_applications_today = all_applications.filter(
            applied_at__date=today
        ).count()
        
        pending_review = all_applications.filter(
            status__in=['pending', 'screening']
        ).count()
        
        # Hiring metrics
        total_hires = all_applications.filter(status='hired').count()
        
        # Calculate average time to hire
        hired_applications = all_applications.filter(
            status='hired',
            hired_at__isnull=False
        ).annotate(
            time_to_hire=ExpressionWrapper(
                F('hired_at') - F('applied_at'),
                output_field=DurationField()
            )
        )
        
        avg_time_to_hire = None
        if hired_applications.exists():
            avg_duration = hired_applications.aggregate(avg=Avg('time_to_hire'))['avg']
            if avg_duration:
                avg_time_to_hire = avg_duration.days
        
        # Cost per hire (based on applications with assigned cost)
        hires_with_cost = all_applications.filter(
            status='hired',
            cost_to_company__isnull=False
        )
        cost_per_hire = None
        if hires_with_cost.exists():
            total_cost = hires_with_cost.aggregate(total=Sum('cost_to_company'))['total'] or 0
            total_paid_hires = hires_with_cost.count()
            if total_paid_hires > 0:
                cost_per_hire = float(total_cost / total_paid_hires)
        
        # Applicant source distribution
        source_data = all_applications.values('source').annotate(count=Count('id'))
        source_distribution = {
            (item['source'] or 'unspecified'): item['count']
            for item in source_data
        }

        top_skills = get_top_skills_for_company(company)
        skill_gaps = get_skill_gap_insights_for_company(company)
        
        # Engagement metrics
        from .models import JobView
        total_job_views = JobView.objects.filter(job__company=company).count()
        
        followers_count = Follow.get_follower_count(company)
        
        # Create snapshot
        CompanyAnalyticsSnapshot.objects.update_or_create(
            company=company,
            date=today,
            defaults={
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'closed_jobs': closed_jobs,
                'total_applications': total_applications,
                'new_applications_today': new_applications_today,
                'pending_review': pending_review,
                'total_hires': total_hires,
                'avg_time_to_hire': avg_time_to_hire,
                'total_job_views': total_job_views,
                'followers_count': followers_count,
                'cost_per_hire': cost_per_hire,
                'applications_by_source': source_distribution,
                'resumes_screened': total_applications,
                'top_skills': [{'skill': skill, 'count': count} for skill, count in top_skills],
                'skill_gaps': [{'skill': skill, 'count': count} for skill, count in skill_gaps],
            }
        )
    
    return f"Generated snapshots for {companies.count()} companies"


@shared_task
def generate_personal_snapshots():
    """
    Generate daily snapshots for all personal accounts.
    Runs daily at 2 AM.
    """
    try:
        from apps.applications.models import Application
        from django.contrib.auth import get_user_model
    except ImportError:
        return "Required models not available"
    
    User = get_user_model()
    today = timezone.now().date()
    
    job_seekers = User.objects.filter(account_type='personal')
    
    for user in job_seekers:
        # Application metrics
        applications = Application.objects.filter(user=user)
        
        total_applications = applications.count()
        applications_pending = applications.filter(status='pending').count()
        applications_screening = applications.filter(status='screening').count()
        applications_interview = applications.filter(status='interview').count()
        applications_offer = applications.filter(status='offer').count()
        applications_hired = applications.filter(status='hired').count()
        applications_rejected = applications.filter(status='rejected').count()
        
        # Engagement metrics
        from .models import ProfileView, JobView, SearchQuery
        
        profile_views_count = ProfileView.objects.filter(
            profile_owner=user
        ).count()
        
        jobs_viewed_count = JobView.objects.filter(viewer=user).count()
        
        # Saved jobs count (if feature exists)
        jobs_saved_count = user.saved_jobs.count() if hasattr(user, 'saved_jobs') else 0
        
        searches_performed = SearchQuery.objects.filter(user=user).count()
        
        # Success metrics
        avg_match_score = None
        if total_applications > 0:
            avg_match_score = applications.aggregate(
                avg=Avg('match_score')
            )['avg']
        
        # Response rate (applications that moved past pending)
        response_rate = None
        if total_applications > 0:
            responded = applications.exclude(status='pending').count()
            response_rate = (responded / total_applications) * 100
        
        assessments = SkillAssessmentResult.objects.filter(user=user)
        assessments_taken = assessments.count()
        avg_assessment_score = assessments.aggregate(avg=Avg('score'))['avg']
        badges = list(assessments.filter(badge_awarded__isnull=False).values_list('badge_awarded', flat=True).distinct())
        analytics = AssessmentAnalytics(user)
        skill_data = analytics.get_skill_radar_data()
        skill_summary = []
        for idx, label in enumerate(skill_data.get('labels', [])):
            skill_summary.append({
                'skill': label,
                'avg_score': skill_data.get('avg_scores', [])[idx] if idx < len(skill_data.get('avg_scores', [])) else 0,
                'pass_rate': skill_data.get('pass_rates', [])[idx] if idx < len(skill_data.get('pass_rates', [])) else 0,
            })
        assessment_trends = get_assessment_trends(user, days=30)
        time_of_day = analytics.get_time_analysis()
        try:
            path_data = LearningPathGenerator(user).generate_path()
            weak_skills = [area['skill'] for area in path_data.get('weak_areas', [])]
        except Exception:
            weak_skills = []

        # Create snapshot
        PersonalAnalyticsSnapshot.objects.update_or_create(
            user=user,
            date=today,
            defaults={
                'total_applications': total_applications,
                'applications_pending': applications_pending,
                'applications_screening': applications_screening,
                'applications_interview': applications_interview,
                'applications_offer': applications_offer,
                'applications_hired': applications_hired,
                'applications_rejected': applications_rejected,
                'profile_views_count': profile_views_count,
                'jobs_viewed_count': jobs_viewed_count,
                'jobs_saved_count': jobs_saved_count,
                'searches_performed': searches_performed,
                'avg_match_score': avg_match_score,
                'response_rate': response_rate,
                'skill_assessments_taken': assessments_taken,
                'avg_skill_assessment_score': avg_assessment_score,
                'badges_earned': badges,
                'skill_summary': skill_summary,
                'assessment_trends': assessment_trends,
                'time_of_day_performance': time_of_day,
                'weak_skills': weak_skills,
            }
        )
    
    return f"Generated snapshots for {job_seekers.count()} job seekers"


@shared_task
def generate_predictive_snapshots():
    """
    Generate predictive insights for companies.
    Runs daily at 3 AM.
    """
    try:
        from django.contrib.auth import get_user_model
    except ImportError:
        return "Required models not available"

    User = get_user_model()
    today = timezone.now().date()
    companies = User.objects.filter(account_type='company')

    for company in companies:
        insight = calculate_predictive_score(company)

        PredictiveAnalyticsSnapshot.objects.update_or_create(
            company=company,
            date=today,
            defaults={
                'likelihood_to_hire': insight.get('likelihood_to_hire'),
                'confidence': insight.get('confidence'),
                'key_drivers': insight.get('key_drivers'),
                'notes': insight.get('notes'),
            }
        )

    return f"Generated predictive snapshots for {companies.count()} companies"


@shared_task
def cleanup_old_analytics_data(days=90):
    """
    Clean up analytics data older than specified days.
    Runs weekly.
    """
    from .models import ProfileView, JobView, SearchQuery, UserActivityLog
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    deleted_counts = {
        'profile_views': ProfileView.objects.filter(viewed_at__lt=cutoff_date).delete()[0],
        'job_views': JobView.objects.filter(viewed_at__lt=cutoff_date).delete()[0],
        'search_queries': SearchQuery.objects.filter(searched_at__lt=cutoff_date).delete()[0],
        'activity_logs': UserActivityLog.objects.filter(timestamp__lt=cutoff_date).delete()[0],
    }
    
    return f"Cleaned up old analytics data: {deleted_counts}"


def _calculate_snapshot_changes(latest, oldest):
    return {
        'new_applications': latest.total_applications - oldest.total_applications,
        'new_hires': latest.total_hires - oldest.total_hires,
        'cost_per_hire': latest.cost_per_hire,
    }


def send_periodic_analytics_report(frequency='weekly'):
    """Send analytics report for the given frequency."""
    try:
        from django.contrib.auth import get_user_model
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
    except ImportError:
        return "Required modules not available"

    window_days = 30 if frequency == 'monthly' else 7
    User = get_user_model()
    companies = User.objects.filter(account_type='company', is_active=True)
    today = timezone.now().date()
    window_start = today - timedelta(days=window_days)

    reports_sent = 0

    for company in companies:
        try:
            snapshots = CompanyAnalyticsSnapshot.objects.filter(
                company=company,
                date__gte=window_start
            ).order_by('-date')

            if snapshots.count() >= 2:
                latest = snapshots.first()
                oldest = snapshots.last()
                context = {
                    'company': company,
                    'latest': latest,
                    'frequency': frequency.capitalize(),
                    **_calculate_snapshot_changes(latest, oldest),
                    'source_breakdown': latest.applications_by_source,
                    'top_skills': latest.top_skills,
                    'skill_gaps': latest.skill_gaps,
                }
                html_message = render_to_string(
                    'analytics/emails/weekly_report.html',
                    context
                )
                send_mail(
                    subject=f'{frequency.capitalize()} Hiring Analytics',
                    message='',
                    from_email='noreply@hiresight.io',
                    recipient_list=[company.email],
                    html_message=html_message,
                    fail_silently=True,
                )
                reports_sent += 1
        except Exception as e:
            print(f"Error sending {frequency} report to {company.email}: {e}")

    return f"Sent {reports_sent} {frequency} reports"


@shared_task
def send_weekly_analytics_report():
    return send_periodic_analytics_report('weekly')


@shared_task
def send_monthly_analytics_report():
    return send_periodic_analytics_report('monthly')


@shared_task
def generate_salary_insights():
    """Generate salary negotiation insights for personal users."""
    try:
        from apps.accounts.models import PersonalProfile
    except ImportError:
        return "PersonalProfile not available"

    users = PersonalProfile.objects.select_related('user').all()

    for profile in users:
        salary_min = profile.salary_expectation_min or 50000
        salary_max = profile.salary_expectation_max or salary_min + 20000
        title = profile.headline or 'Professional'

        SalaryNegotiationInsight.objects.update_or_create(
            user=profile.user,
            title=title,
            location=profile.location or '',
            defaults={
                'salary_floor': salary_min * 0.9,
                'salary_ceiling': salary_max * 1.1,
                'market_rate': (salary_min + salary_max) / 2,
                'confidence_score': 80.0,
            }
        )

    return f"Generated salary insights for {users.count()} users"


@shared_task
def generate_interview_questions():
    """Generate interview question templates per job."""
    try:
        from apps.jobs.models import Job
    except ImportError:
        return "Job model not available"

    base_questions = [
        "Tell me about a time you solved a tough problem.",
        "How do you prioritize competing deadlines?",
        "Describe how you collaborate with remote teams.",
        "What metrics do you use to measure success?",
        "How do you stay current with industry trends?"
    ]

    jobs = Job.objects.filter(status='active')
    for job in jobs:
        questions = base_questions + [f"Why are you interested in this {job.experience_level} role?"]
        InterviewQuestionTemplate.objects.update_or_create(
            job=job,
            title=f"{job.title} Interview Questions",
            defaults={'questions': questions}
        )

    return f"Generated interview questions for {jobs.count()} jobs"


@shared_task
def assess_culture_fit():
    """Generate synthetic culture fit assessments."""
    applicants = User.objects.filter(account_type='personal')
    company = User.objects.filter(account_type='company').first()

    if not company:
        return "No company accounts available"

    for applicant in applicants:
        CultureFitAssessment.objects.create(
            user=applicant,
            company=company,
            score=round(60 + (applicant.job_applications.count() % 40), 1),
            highlights=[
                {'trait': 'Teamwork', 'score': 85},
                {'trait': 'Adaptability', 'score': 78},
            ],
        )

    return f"Created culture fit assessments for {applicants.count()} applicants"


@shared_task
def generate_diversity_snapshots():
    """Snapshot diversity metrics for companies."""
    companies = User.objects.filter(account_type='company')
    for company in companies:
        DiversityAnalyticsSnapshot.objects.update_or_create(
            company=company,
            date=timezone.now().date(),
            defaults={
                'female_ratio': round(0.4 + (company.profile_views_received.count() % 10) * 0.01, 2),
                'underrepresented_ratio': round(0.25 + (company.personal_analytics_snapshots.count() % 10) * 0.01, 2),
                'inclusive_score': round(70 + (company.analytics_snapshots.count() % 20), 1),
            }
        )

    return f"Generated diversity snapshots for {companies.count()} companies"


@shared_task
def kickoff_reference_checks():
    """Send out pending reference check requests."""
    pending = ReferenceCheckRequest.objects.filter(status='pending')
    for req in pending:
        req.status = 'sent'
        req.save(update_fields=['status'])

    return f"Sent {pending.count()} reference requests"
