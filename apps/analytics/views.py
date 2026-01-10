from django.shortcuts import render
from django.db.models import Count
from apps.jobs.models import Job
from apps.applications.models import Application


def analytics_dashboard(request):
    # Example stats
    total_jobs = Job.objects.count()
    total_applications = Application.objects.count()
    applications_per_job = Application.objects.values('job').annotate(count=Count('id'))
    return render(request, 'analytics/analytics.html', {
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'applications_per_job': applications_per_job,
    })