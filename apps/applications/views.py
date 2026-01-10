from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def my_applications(request):
    """Placeholder view for user's applications."""
    return render(request, 'applications/my_applications.html', {
        'title': 'My Applications',
        'message': 'Application tracking functionality coming soon!'
    })

@login_required
def application_detail(request, pk):
    """Placeholder view for application detail."""
    return render(request, 'applications/detail.html', {
        'title': 'Application Detail',
        'message': 'Application detail functionality coming soon!',
        'application_id': pk
    })

@login_required
def apply_for_job(request, job_id):
    """Placeholder view for applying to a job."""
    return render(request, 'applications/apply.html', {
        'title': 'Apply for Job',
        'message': 'Job application functionality coming soon!',
        'job_id': job_id
    })

@login_required
def applicants(request):
    """Placeholder view for viewing applicants."""
    return render(request, 'applications/applicants.html', {
        'title': 'Applicants',
        'message': 'Applicant management functionality coming soon!'
    })