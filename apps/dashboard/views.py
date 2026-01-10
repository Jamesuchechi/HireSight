from django.shortcuts import render, redirect
from django.utils import timezone
from apps.accounts.decorators import personal_required, company_required

# TODO: Uncomment when Application and Job models are implemented
# from apps.applications.models import Application
# from apps.jobs.models import Job
from apps.resumes.models import Resume


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard_home')
    return render(request, 'landing/index.html')


def _get_personal_context(request):
    # TODO: Uncomment when Application model is implemented
    # total_apps = Application.objects.filter(user=request.user).count()
    # pending = Application.objects.filter(user=request.user, status='pending').count()
    # apps_qs = Application.objects.filter(user=request.user).order_by('-applied_at')[:5]
    total_apps = 0
    pending = 0
    apps_qs = []

    saved_jobs_attr = getattr(request.user, 'saved_jobs', None)
    saved_jobs = saved_jobs_attr.all()[:3] if saved_jobs_attr is not None else []
    recommended = []
    profile = getattr(request.user, 'personal_profile', None)
    try:
        profile_completion = profile.calculate_completion_score() if profile and hasattr(profile, 'calculate_completion_score') else 100
    except Exception:
        profile_completion = 100

    context = {
        'stats': [
            {'label': 'Total Applications', 'value': total_apps, 'icon': 'send', 'color': 'blue'},
            {'label': 'Pending Reviews', 'value': pending, 'icon': 'clock', 'color': 'gold'},
            {'label': 'Interviews', 'value': 0, 'icon': 'calendar', 'color': 'cyan'},
            {'label': 'Success Rate', 'value': '0%', 'icon': 'trending-up', 'color': 'green'},
        ],
        'applications': apps_qs,
        'saved_jobs': saved_jobs,
        'recommended_jobs': recommended,
        'upcoming_interviews': [],
        'profile_completion_score': profile_completion,
        'activities': [],
    }
    return context


def _get_company_context(request):
    # TODO: Uncomment when Job and Application models are implemented
    # active_jobs = Job.objects.filter(company=request.user).count()
    # total_apps = Application.objects.filter(job__company=request.user).count()
    # jobs_qs = Job.objects.filter(company=request.user)[:4]
    active_jobs = 0
    total_apps = 0
    jobs_qs = []
    avg_match = 0
    candidates = []

    context = {
        'stats': [
            {'label': 'Active Jobs', 'value': active_jobs, 'icon': 'briefcase', 'color': 'blue'},
            {'label': 'Total Applications', 'value': total_apps, 'icon': 'users', 'color': 'cyan'},
            {'label': 'Avg Match Score', 'value': avg_match, 'icon': 'target', 'color': 'gold'},
            {'label': 'Time Saved', 'value': '0h', 'icon': 'zap', 'color': 'green'},
        ],
        'candidates': candidates,
        'active_jobs': jobs_qs,
        'upcoming_interviews': [],
        'activities': [],
    }
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


@personal_required
def personal_dashboard(request):
    context = _get_personal_context(request)
    return render(request, 'dashboard/personal_dashboard.html', context)


@company_required
def company_dashboard(request):
    context = _get_company_context(request)
    return render(request, 'dashboard/company_dashboard.html', context)