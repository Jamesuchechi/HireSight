from datetime import timedelta
from io import BytesIO
from django.template.loader import render_to_string
from django.core.mail import EmailMessage, send_mail
from django.utils import timezone
from celery import shared_task

from .models import Interview


def _build_ics(interview):
    start = interview.scheduled_date
    end = interview.get_end_time()
    uid = f"interview-{interview.id}@hiresight.io"
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//HireSight Interview//hiresight.io//',
        'METHOD:REQUEST',
        'BEGIN:VEVENT',
        f'UID:{uid}',
        f'DTSTAMP:{timezone.now().strftime("%Y%m%dT%H%M%SZ")}',
        f'DTSTART:{start.strftime("%Y%m%dT%H%M%SZ")}',
        f'DTEND:{end.strftime("%Y%m%dT%H%M%SZ")}',
        f'SUMMARY:Interview with {interview.application.job.company.company_name}',
        f'DESCRIPTION:{interview.candidate_instructions}',
        f'LOCATION:{interview.location or interview.video_link or "Online"}',
        'END:VEVENT',
        'END:VCALENDAR',
    ]
    return '\r\n'.join(lines).encode('utf-8')


@shared_task
def send_interview_invitation(interview_id, is_reschedule=False):
    try:
        interview = Interview.objects.select_related(
            'application__applicant',
            'application__job__company'
        ).get(id=interview_id)
    except Interview.DoesNotExist:
        return

    candidate = interview.application.applicant
    company = interview.application.job.company
    context = {
        'interview': interview,
        'candidate': candidate,
        'company': company,
        'is_reschedule': is_reschedule,
    }
    subject = f"{'Rescheduled' if is_reschedule else 'Interview'} Invitation - {interview.application.job.title}"
    message = render_to_string('interviews/emails/invitation.html', context)
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email='noreply@hiresight.io',
        to=[candidate.email],
        cc=[interview.interviewer_email],
    )
    ics = _build_ics(interview)
    email.attach('interview.ics', ics, 'text/calendar')
    email.content_subtype = 'html'
    email.send(fail_silently=True)


def _send_reminder_email(interview, timeframe):
    context = {
        'interview': interview,
        'timeframe': timeframe,
    }
    subject = f"Interview Reminder: {interview.application.job.title} in {timeframe}"
    message = render_to_string('interviews/emails/reminder.html', context)
    send_mail(
        subject=subject,
        message=message,
        from_email='noreply@hiresight.io',
        recipient_list=[interview.application.applicant.email],
        fail_silently=True,
    )


@shared_task
def send_interview_reminders():
    now = timezone.now()
    for hours, flag_field in [(24, 'reminder_24h_sent'), (1, 'reminder_1h_sent')]:
        window_start = now + timedelta(hours=hours) - timedelta(minutes=15)
        window_end = now + timedelta(hours=hours) + timedelta(minutes=15)
        interviews = Interview.objects.filter(
            scheduled_date__range=(window_start, window_end),
            status__in=[Interview.InterviewStatus.SCHEDULED, Interview.InterviewStatus.RESCHEDULED],
            **{flag_field: False}
        )
        for interview in interviews:
            _send_reminder_email(interview, f"{hours} hours")
            setattr(interview, flag_field, True)
            interview.save(update_fields=[flag_field])


@shared_task
def send_interview_cancellation(interview_id):
    try:
        interview = Interview.objects.select_related(
            'application__applicant',
            'application__job__company'
        ).get(id=interview_id)
    except Interview.DoesNotExist:
        return

    candidate = interview.application.applicant
    context = {
        'interview': interview,
        'candidate': candidate,
    }
    subject = f"Interview Cancelled: {interview.application.job.title}"
    message = render_to_string('interviews/emails/cancellation.html', context)
    recipients = [candidate.email]
    if interview.interviewer_email:
        recipients.append(interview.interviewer_email)
    send_mail(
        subject=subject,
        message=message,
        from_email='noreply@hiresight.io',
        recipient_list=recipients,
        fail_silently=True,
    )
