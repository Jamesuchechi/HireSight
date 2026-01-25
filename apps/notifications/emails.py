from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

def _build_absolute_url(path: str) -> str:
    """Ensure a fully qualified URL using SITE_URL."""
    base = getattr(settings, 'SITE_URL', '').rstrip('/')
    return f"{base}{path}" if base else path


def _notification_helpers():
    """Lazy import to avoid AppRegistry issues during startup."""
    from .models import NotificationType
    from .signals import notification_create

    return NotificationType, notification_create


def send_practice_ready_email(session):
    """Notify the candidate that AI questions are ready."""
    question_count = session.questions.count()
    dashboard_path = reverse('interviews:practice_dashboard')
    dashboard_link = _build_absolute_url(dashboard_path)
    subject = "Your Interview Practice Session is Ready!"
    message = (
        f"Hi {session.candidate.get_full_name() or session.candidate.email},\n\n"
        f"We've generated {question_count} interview questions for your practice session.\n"
        f"Head to the dashboard to start practicing: {dashboard_link}\n\n"
        "Good luck!"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[session.candidate.email],
        fail_silently=True,
    )

    NotificationType, notification_create = _notification_helpers()
    notification_create.send(
        sender=send_practice_ready_email,
        user=session.candidate,
        title=subject,
        message=f"{question_count} questions are ready. Tap to begin practicing.",
        link=dashboard_link,
        notification_type=NotificationType.SYSTEM,
        action_text="Open practice dashboard",
    )


def send_report_ready_email(session):
    """Notify the candidate that the performance report is available."""
    report = getattr(session, 'performance_report', None)
    overall_score = report.overall_score if report else session.overall_score or 0
    strengths = report.strengths if report else []
    top_strength = strengths[0] if strengths else 'Strong performance'
    report_path = reverse('interviews:practice_report', kwargs={'session_id': session.id})
    report_link = _build_absolute_url(report_path)
    subject = "Your Interview Performance Report is Ready"
    message = (
        f"Hi {session.candidate.get_full_name() or session.candidate.email},\n\n"
        f"Your report is ready with an overall score of {overall_score}.\n"
        f"Top strength: {top_strength}\n"
        f"View the full report here: {report_link}\n\n"
        "Keep the momentum going!"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[session.candidate.email],
        fail_silently=True,
    )

    NotificationType, notification_create = _notification_helpers()
    notification_create.send(
        sender=send_report_ready_email,
        user=session.candidate,
        title=subject,
        message=f"Overall score {overall_score}. {top_strength}",
        link=report_link,
        notification_type=NotificationType.SYSTEM,
        action_text="View report",
    )


def send_milestone_email(user, milestone):
    """Celebrate milestone of completed practice sessions."""
    dashboard_path = reverse('interviews:practice_dashboard')
    dashboard_link = _build_absolute_url(dashboard_path)
    subject = f"Congratulations! You've completed {milestone} practice sessions"
    message = (
        f"🏅 Well done, {user.get_full_name() or user.email}!\n\n"
        f"You've completed {milestone} practice sessions. Keep sharpening your skills and "
        f"dive into the next session: {dashboard_link}\n\n"
        "Every session brings you closer to your dream role."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )

    NotificationType, notification_create = _notification_helpers()
    notification_create.send(
        sender=send_milestone_email,
        user=user,
        title=subject,
        message="Badge unlocked! Keep the streak going.",
        link=dashboard_link,
        notification_type=NotificationType.SYSTEM,
        action_text="View dashboard",
    )
