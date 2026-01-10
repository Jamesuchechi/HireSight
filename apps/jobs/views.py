from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def browse_jobs(request):
    """Placeholder view for browsing jobs."""
    return render(request, 'jobs/browse.html', {
        'title': 'Browse Jobs',
        'message': 'Job browsing functionality coming soon!'
    })

@login_required
def saved_jobs(request):
    """Placeholder view for saved jobs."""
    return render(request, 'jobs/saved.html', {
        'title': 'Saved Jobs',
        'message': 'Saved jobs functionality coming soon!'
    })

@login_required
def job_detail(request, pk):
    """Placeholder view for job detail."""
    return render(request, 'jobs/detail.html', {
        'title': 'Job Detail',
        'message': 'Job detail functionality coming soon!',
        'job_id': pk
    })

@login_required
def manage_jobs(request):
    """Placeholder view for managing jobs."""
    return render(request, 'jobs/manage.html', {
        'title': 'Manage Jobs',
        'message': 'Job management functionality coming soon!'
    })