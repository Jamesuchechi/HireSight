from django.shortcuts import render
from django.db.models import Count

# TODO: Uncomment when Job and Application models are implemented
# from apps.jobs.models import Job
# from apps.applications.models import Application


def analytics_dashboard(request):
    # TODO: Uncomment when models are implemented
    # total_jobs = Job.objects.count()
    # total_applications = Application.objects.count()
    total_jobs = 0
    total_applications = 0
    applications_per_job = Application.objects.values('job').annotate(count=Count('id'))
    return render(request, 'analytics/analytics.html', {
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'applications_per_job': applications_per_job,
    })