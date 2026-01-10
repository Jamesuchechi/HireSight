from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def upload(request):
    """Placeholder view for resume screening upload."""
    return render(request, 'screening/upload.html', {
        'title': 'Resume Screening',
        'message': 'AI-powered resume screening functionality coming soon!'
    })