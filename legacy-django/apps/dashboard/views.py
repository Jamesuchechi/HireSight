from io import BytesIO

from django.shortcuts import render, redirect
from django.utils import timezone
from django.db import models
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from apps.accounts.decorators import personal_required, company_required
from apps.applications.models import Application, ApplicationStatus
from apps.applications.utils import build_pipeline_data
from apps.assessments.analytics_helpers import get_company_candidate_insights
from apps.assessments.models import SkillBadge, SkillTest
from apps.assessments.recommendations import TestRecommendationEngine
from apps.jobs.models import Job, JobStatus
from apps.jobs.recommendations import JobRecommendationEngine
from apps.messaging.models import Message
from apps.resumes.models import Resume
from apps.interviews.models import Interview


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard_home')
    return render(request, 'landing/index.html')


def _get_personal_context(request):
    user = request.user
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timezone.timedelta(days=7)

    apps_qs = Application.objects.filter(applicant=user).select_related('job', 'job__company')
    total_apps = apps_qs.count()
    applications_submitted = apps_qs.filter(applied_at__gte=month_start).count()
    applications_this_week = apps_qs.filter(applied_at__gte=week_ago).count()
    interviews_scheduled = apps_qs.filter(status=ApplicationStatus.INTERVIEW).count()
    recent_applications = apps_qs.order_by('-applied_at')[:10]
    upcoming_interview = apps_qs.filter(status=ApplicationStatus.INTERVIEW).order_by('applied_at').first()

    saved_jobs_attr = getattr(user, 'saved_jobs', None)
    saved_jobs = saved_jobs_attr.all()[:3] if saved_jobs_attr is not None else []
    saved_jobs_count = saved_jobs_attr.count() if saved_jobs_attr is not None else 0

    profile = getattr(user, 'personal_profile', None)
    profile_completion = 100
    if profile and hasattr(profile, 'calculate_completion_score'):
        try:
            profile_completion = profile.calculate_completion_score()
        except Exception:
            profile_completion = 100
    else:
        profile_completion = 0

    engine = TestRecommendationEngine()
    pending_recommendations = engine.recommend_for_user(user, limit=5)

    profile_views_last_30 = user.get_profile_views_count(days=30) if user.account_type == 'personal' else 0
    prev_period_start = now - timezone.timedelta(days=60)
    prev_period_end = now - timezone.timedelta(days=30)
    previous_views = 0
    if user.account_type == 'personal':
        previous_views = user.profile_views_received.filter(
            viewed_at__gte=prev_period_start,
            viewed_at__lt=prev_period_end
        ).count()
    if previous_views > 0:
        profile_views_change = round(((profile_views_last_30 - previous_views) / previous_views) * 100)
    else:
        profile_views_change = profile_views_last_30

    stats = {
        'applications_submitted': applications_submitted,
        'applications_this_week': applications_this_week,
        'interviews_scheduled': interviews_scheduled,
        'profile_views': profile_views_last_30,
        'profile_views_change': profile_views_change,
        'saved_jobs': saved_jobs_count,
    }
    stats_cards = [
        {'label': 'Applications Submitted', 'value': applications_submitted, 'icon': 'send', 'color': 'blue'},
        {'label': 'Interviews Scheduled', 'value': interviews_scheduled, 'icon': 'calendar', 'color': 'secondary'},
        {'label': 'Profile Views', 'value': profile_views_last_30, 'icon': 'eye', 'color': 'accent'},
        {'label': 'Saved Jobs', 'value': saved_jobs_count, 'icon': 'bookmark', 'color': 'purple'},
    ]

    new_jobs_count = Job.objects.filter(
        status=JobStatus.ACTIVE,
        created_at__date=now.date()
    ).count()

    unread_messages = Message.objects.filter(
        conversation__participants=user
    ).exclude(sender=user).count()

    recommendations = []
    recommended_limit = 5
    if profile:
        engine = JobRecommendationEngine()
        job_candidates = Job.objects.filter(status=JobStatus.ACTIVE).select_related('company').order_by('-published_at')[:20]
        for job in job_candidates:
            score = round(engine.calculate_match_score(user, job) * 100)
            job.match_score = score if score else 60
            recommendations.append(job)
            if len(recommendations) >= recommended_limit:
                break
    if len(recommendations) < recommended_limit:
        fallback_jobs = Job.objects.filter(status=JobStatus.ACTIVE).select_related('company').order_by('-views_count')[:recommended_limit]
        seen_ids = {job.id for job in recommendations}
        for job in fallback_jobs:
            if job.id in seen_ids:
                continue
            job.match_score = getattr(job, 'match_score', 70)
            recommendations.append(job)
            if len(recommendations) >= recommended_limit:
                break

    upcoming_interviews_qs = Interview.objects.filter(
        application__applicant=user,
        scheduled_date__gte=now,
        status__in=[Interview.InterviewStatus.SCHEDULED, Interview.InterviewStatus.RESCHEDULED]
    ).select_related('application__job__company')[:5]

    context = {
        'stats': stats,
        'stats_cards': stats_cards,
        'applications': recent_applications,
        'recent_applications': recent_applications,
        'saved_jobs': saved_jobs,
        'saved_jobs_count': saved_jobs_count,
        'recommended_jobs': recommendations,
        'upcoming_interviews': upcoming_interviews_qs,
        'profile_completion': profile_completion,
        'profile_completion_score': profile_completion,
        'activities': apps_qs.order_by('-last_activity_at')[:5],
        'next_interview': upcoming_interview,
        'new_jobs_count': new_jobs_count,
        'unread_messages': unread_messages,
        'skill_badges': request.user.skill_badges.select_related('test')[:4] if hasattr(request.user, 'skill_badges') else [],
    }
    context['recent_badges'] = SkillBadge.objects.filter(
        user=user
    ).select_related('test', 'attempt').order_by('-issued_at')[:3]
    context['pending_recommendations'] = pending_recommendations
    return context


def _get_company_context(request):
    # Get company applications and jobs
    company_jobs = Job.objects.filter(company=request.user.company_profile)
    active_jobs = company_jobs.filter(status=JobStatus.ACTIVE).count()
    total_apps = Application.objects.filter(job__company=request.user.company_profile).count()

    # Calculate application statistics
    today = timezone.now().date()
    week_ago = today - timezone.timedelta(days=7)
    month_ago = today - timezone.timedelta(days=30)

    # Applications by status
    apps_by_status = Application.objects.filter(job__company=request.user.company_profile).values('status').annotate(
        count=models.Count('id')
    ).order_by('status')

    # Recent applications (last 7 days)
    recent_apps = Application.objects.filter(
        job__company=request.user.company_profile,
        applied_at__date__gte=week_ago
    ).count()

    # Applications this month
    monthly_apps = Application.objects.filter(
        job__company=request.user.company_profile,
        applied_at__date__gte=month_ago
    ).count()

    # Average match score
    avg_match = Application.objects.filter(
        job__company=request.user.company_profile,
        match_score__isnull=False
    ).aggregate(avg=models.Avg('match_score'))['avg']
    avg_match = round(avg_match) if avg_match else 0

    # Top candidates (highest match scores)
    top_candidates = Application.objects.filter(
        job__company=request.user.company_profile,
        match_score__isnull=False
    ).select_related(
        'applicant__personal_profile',
        'job'
    ).order_by('-match_score')[:5]

    company_apps = Application.objects.filter(job__company=request.user.company_profile)
    pipeline_data = build_pipeline_data(company_apps)

    # Recent activity (last 10 status changes)
    recent_activity = Application.objects.filter(
        job__company=request.user.company_profile
    ).select_related(
        'applicant__personal_profile',
        'job'
    ).order_by('-status_changed_at')[:10]

    # Jobs with most applications
    jobs_with_apps = company_jobs.annotate(
        app_count=models.Count('applications'),
        screening_count=models.Count('applications__status', filter=models.Q(applications__status='screening')),
        interview_count=models.Count('applications__status', filter=models.Q(applications__status='interview'))
    ).order_by('-app_count')[:4]

    month_start_date = today.replace(day=1)
    stats = {
        'active_jobs': active_jobs,
        'jobs_this_month': company_jobs.filter(created_at__date__gte=month_start_date).count(),
        'total_applications': total_apps,
        'applications_this_week': recent_apps,
        'avg_match_score': f"{avg_match}%",
        'interviews_scheduled': Application.objects.filter(
            job__company=request.user.company_profile,
            status=ApplicationStatus.INTERVIEW
        ).count(),
    }
    stats_cards = [
        {'label': 'Active Jobs', 'value': active_jobs, 'icon': 'briefcase', 'color': 'blue'},
        {'label': 'Total Applications', 'value': total_apps, 'icon': 'users', 'color': 'cyan'},
        {'label': 'Avg Match Score', 'value': f"{avg_match}%", 'icon': 'target', 'color': 'gold'},
        {'label': 'This Week', 'value': recent_apps, 'icon': 'trending-up', 'color': 'green'},
    ]

    context = {
        'stats': stats,
        'stats_cards': stats_cards,
        'candidates': top_candidates,
        'top_candidates': top_candidates,
        'active_jobs': jobs_with_apps,
        'pipeline_stats': pipeline_data['stats'],
        'pipeline_stage_summary': pipeline_data['stage_summary'],
        'pipeline_history_summary': pipeline_data['history_summary'],
        'recent_activity': recent_activity,
        'applications_this_week': recent_apps,
        'applications_this_month': monthly_apps,
        'total_applications': total_apps,
        'new_today': Application.objects.filter(
            job__company=request.user.company_profile,
            applied_at__date=today
        ).count(),
        'interviews_scheduled': stats['interviews_scheduled'],
        'avg_time_to_hire': 12,  # TODO: Calculate actual average time to hire
        'upcoming_interviews': [],  # TODO: Implement upcoming interviews
        'activities': recent_activity,
    }
    context['candidate_insights'] = get_company_candidate_insights(request.user.company_profile) if request.user.company_profile else {}
    return context


def dashboard_home(request):
    if not request.user.is_authenticated:
        return redirect('home')

    if request.user.account_type == 'personal':
        ctx = _get_personal_context(request)
        return render(request, 'dashboard/personal_dashboard.html', ctx)

    if request.user.account_type == 'company':
        ctx = _get_company_context(request)
        return render(request, 'dashboard/company_dashboard.html', ctx)

    # Default fallback
    return redirect('dashboard:landing')


@login_required
def export_dashboard_pdf(request):
    context_provider = _get_personal_context if request.user.account_type == 'personal' else _get_company_context
    context = context_provider(request)
    title = request.user.get_full_name() if request.user.account_type == 'personal' else getattr(request.user.company_profile, 'company_name', 'Company')
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont('Helvetica-Bold', 18)
    pdf.drawString(72, 760, f"{title} Dashboard Snapshot")
    pdf.setFont('Helvetica', 11)
    y = 720
    stats_cards = context.get('stats_cards')
    if not stats_cards:
        stats_source = context.get('stats', [])
        if isinstance(stats_source, dict):
            stats_cards = [{'label': key.replace('_', ' ').title(), 'value': value} for key, value in stats_source.items()]
        else:
            stats_cards = stats_source
    if stats_cards:
        for stat in stats_cards:
            label = stat.get('label')
            value = stat.get('value')
            pdf.drawString(72, y, f"{label}: {value}")
            y -= 20
    else:
        pdf.drawString(72, y, "No stats available yet.")
        y -= 20

    pdf.setFont('Helvetica', 10)
    pdf.drawString(72, y - 10, f"Generated: {timezone.now().strftime('%B %d, %Y %I:%M %p')}")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=dashboard_snapshot.pdf'
    return response


@personal_required
def personal_dashboard(request):
    context = _get_personal_context(request)
    return render(request, 'dashboard/personal_dashboard.html', context)


@company_required
def company_dashboard(request):
    context = _get_company_context(request)
    return render(request, 'dashboard/company_dashboard.html', context)
