from django.urls import reverse

from .models import Interview


def interview_navigation_context(request):
    """Provide interview-related counts and links for the sidebar."""
    if not request.user.is_authenticated:
        return {}

    nav_link = reverse('interviews:upcoming')
    schedule_link = ''
    can_schedule = False
    practice_nav_link = ''

    if request.user.account_type == 'company':
        nav_link = reverse('interviews:list')
        schedule_link = reverse('applications:manage')
        can_schedule = True
        upcoming_count = Interview.objects.upcoming().filter(
            application__job__company__user=request.user
        ).count()
    else:
        upcoming_count = Interview.objects.upcoming().filter(
            application__applicant=request.user
        ).count()
        practice_nav_link = reverse('interviews:practice_dashboard')
        practice_nav_link = reverse('interviews:practice_dashboard')

    return {
        'interview_nav_link': nav_link,
        'interview_schedule_url': schedule_link,
        'show_interview_schedule_action': can_schedule,
        'upcoming_interviews_count': upcoming_count,
        'practice_nav_link': practice_nav_link if request.user.account_type == 'personal' else '',
        'show_practice_link': request.user.account_type == 'personal',
    }
