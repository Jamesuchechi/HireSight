from django.urls import reverse

from .models import Interview


def interview_navigation_context(request):
    """Provide interview-related counts and links for the sidebar."""
    if not request.user.is_authenticated:
        return {}

    nav_link = reverse('interviews:upcoming')
    schedule_link = ''
    can_schedule = False

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

    return {
        'interview_nav_link': nav_link,
        'interview_schedule_url': schedule_link,
        'show_interview_schedule_action': can_schedule,
        'upcoming_interviews_count': upcoming_count,
    }
