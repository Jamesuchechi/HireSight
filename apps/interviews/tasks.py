from datetime import timedelta
from io import BytesIO
from django.db import transaction
from django.template.loader import render_to_string
from django.core.mail import EmailMessage, send_mail
from django.utils import timezone
from django.conf import settings
from celery import shared_task
import logging

from .models import Interview

logger = logging.getLogger(__name__)


def _build_ics(interview):
    """
    Build iCalendar (.ics) file content for an interview
    
    Args:
        interview: Interview instance
    
    Returns:
        bytes: ICS file content
    """
    start = interview.scheduled_date
    end = interview.get_end_time()
    uid = f"interview-{interview.id}@hiresight.io"
    
    # Build attendees list
    attendees = [
        f"ATTENDEE;CN={interview.application.applicant.email};RSVP=TRUE:mailto:{interview.application.applicant.email}",
        f"ATTENDEE;CN={interview.interviewer_email};ROLE=REQ-PARTICIPANT:mailto:{interview.interviewer_email}",
    ]
    
    # Add additional interviewers
    for interviewer in interview.additional_interviewers:
        if interviewer.get('email'):
            attendees.append(
                f"ATTENDEE;CN={interviewer.get('email')};ROLE=OPT-PARTICIPANT:mailto:{interviewer.get('email')}"
            )
    
    # Determine location
    if interview.video_link:
        location = interview.video_link
    elif interview.location:
        location = interview.location
    else:
        location = "Online"
    
    # Build description
    description = f"{interview.candidate_instructions}\\n\\n"
    if interview.video_link:
        description += f"Join via: {interview.video_link}\\n"
    if interview.dial_in_number:
        description += f"Dial-in: {interview.dial_in_number}\\n"
    
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//HireSight Interview//hiresight.io//',
        'METHOD:REQUEST',
        'CALSCALE:GREGORIAN',
        'BEGIN:VEVENT',
        f'UID:{uid}',
        f'DTSTAMP:{timezone.now().strftime("%Y%m%dT%H%M%SZ")}',
        f'DTSTART:{start.strftime("%Y%m%dT%H%M%SZ")}',
        f'DTEND:{end.strftime("%Y%m%dT%H%M%SZ")}',
        f'SUMMARY:Interview: {interview.application.job.title}',
        f'DESCRIPTION:{description}',
        f'LOCATION:{location}',
        f'STATUS:CONFIRMED',
        f'SEQUENCE:{interview.reschedule_count}',
        f'ORGANIZER;CN={interview.interviewer_email}:mailto:{interview.interviewer_email}',
    ]
    
    # Add attendees
    lines.extend(attendees)
    
    # Add reminder (15 minutes before)
    lines.extend([
        'BEGIN:VALARM',
        'TRIGGER:-PT15M',
        'ACTION:DISPLAY',
        'DESCRIPTION:Interview reminder',
        'END:VALARM',
    ])
    
    lines.extend([
        'END:VEVENT',
        'END:VCALENDAR',
    ])
    
    return '\r\n'.join(lines).encode('utf-8')


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_interview_invitation(self, interview_id, is_reschedule=False):
    """
    Send interview invitation email to candidate and interviewer
    
    Args:
        interview_id: UUID of the interview
        is_reschedule: Boolean indicating if this is a reschedule notification
    """
    try:
        interview = Interview.objects.select_related(
            'application__applicant',
            'application__applicant__personalprofile',
            'application__job__company',
        ).get(id=interview_id)
    except Interview.DoesNotExist:
        logger.error(f"Interview {interview_id} not found for invitation email")
        return
    
    candidate = interview.application.applicant
    company = interview.application.job.company
    
    # Get candidate name
    try:
        candidate_name = candidate.personalprofile.full_name
    except:
        candidate_name = candidate.email
    
    # Build context
    context = {
        'interview': interview,
        'candidate': candidate,
        'candidate_name': candidate_name,
        'company': company,
        'is_reschedule': is_reschedule,
        'calendar_url': interview.get_calendar_event_url(),
    }
    
    # Determine subject
    if is_reschedule:
        subject = f"Interview Rescheduled: {interview.application.job.title}"
    else:
        subject = f"Interview Invitation: {interview.application.job.title}"
    
    # Render email
    try:
        html_message = render_to_string('interviews/emails/invitation.html', context)
        text_message = render_to_string('interviews/emails/invitation.txt', context)
    except Exception as e:
        logger.error(f"Failed to render email template: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e)
    
    # Build recipient list
    recipients = [candidate.email]
    cc_list = []
    
    if interview.interviewer_email:
        cc_list.append(interview.interviewer_email)
    
    # Add additional interviewers to CC
    for interviewer in interview.additional_interviewers:
        if interviewer.get('email'):
            cc_list.append(interviewer.get('email'))
    
    # Create email
    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
        cc=cc_list,
    )
    
    # Attach calendar invite
    try:
        ics = _build_ics(interview)
        email.attach('interview.ics', ics, 'text/calendar')
    except Exception as e:
        logger.warning(f"Failed to attach ICS file: {e}")
        # Continue without ICS attachment
    
    email.content_subtype = 'html'
    
    # Send email
    try:
        email.send(fail_silently=False)
        logger.info(f"Interview invitation sent for interview {interview_id}")
    except Exception as e:
        logger.error(f"Failed to send interview invitation: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_candidate_reschedule_request_email(self, interview_id, proposal_entry):
    """
    Notify the company that a candidate requested a reschedule
    """
    try:
        interview = Interview.objects.select_related(
            'application__applicant',
            'application__job__company',
        ).get(id=interview_id)
    except Interview.DoesNotExist:
        logger.error(f"Interview {interview_id} not found for reschedule notification")
        return

    candidate = interview.application.applicant
    company = interview.application.job.company

    try:
        candidate_name = candidate.personalprofile.full_name
    except Exception:
        candidate_name = candidate.email

    proposal_date = proposal_entry.get('date')
    try:
        proposal_dt = timezone.datetime.fromisoformat(proposal_date)
        proposal_display = timezone.localtime(proposal_dt).strftime('%b %d, %Y at %I:%M %p %Z')
    except Exception:
        proposal_display = proposal_date

    context = {
        'interview': interview,
        'candidate_name': candidate_name,
        'company': company,
        'proposal': proposal_entry,
        'proposal_display': proposal_display,
        'detail_link': f"{getattr(settings, 'SITE_URL', 'https://hiresight.io').rstrip('/')}/interviews/{interview.id}/"
    }

    subject = f"{candidate_name} requested to reschedule {interview.application.job.title}"

    try:
        html_message = render_to_string('interviews/emails/reschedule_request.html', context)
        text_message = render_to_string('interviews/emails/reschedule_request.txt', context)
    except Exception as e:
        logger.error(f"Failed to render reschedule request email template: {e}")
        raise self.retry(exc=e)

    try:
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[company.user.email],
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)
        logger.info(f"Reschedule request email sent for interview {interview_id}")
    except Exception as e:
        logger.error(f"Failed to send reschedule request email: {e}")
        raise self.retry(exc=e)


def _send_reminder_email(interview, timeframe):
    """
    Send reminder email for upcoming interview
    
    Args:
        interview: Interview instance
        timeframe: String describing time until interview (e.g., "24 hours")
    """
    candidate = interview.application.applicant
    
    # Get candidate name
    try:
        candidate_name = candidate.personalprofile.full_name
    except:
        candidate_name = candidate.email
    
    context = {
        'interview': interview,
        'candidate': candidate,
        'candidate_name': candidate_name,
        'timeframe': timeframe,
        'calendar_url': interview.get_calendar_event_url(),
    }
    
    subject = f"Interview Reminder: {interview.application.job.title} in {timeframe}"
    
    try:
        html_message = render_to_string('interviews/emails/reminder.html', context)
        text_message = render_to_string('interviews/emails/reminder.txt', context)
        
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[candidate.email],
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)
        
        logger.info(f"Reminder sent for interview {interview.id} ({timeframe})")
    except Exception as e:
        logger.error(f"Failed to send reminder email: {e}")


@shared_task
def send_interview_reminders():
    """
    Send reminder emails for upcoming interviews
    Runs periodically via Celery Beat
    """
    # 24-hour reminders
    interviews_24h = Interview.objects.needing_24h_reminder()
    sent_24h = 0
    for interview in interviews_24h:
        try:
            with transaction.atomic():
                locked = Interview.objects.select_for_update().get(pk=interview.pk)
                if locked.reminder_24h_sent:
                    continue
                _send_reminder_email(locked, "24 hours")
                locked.reminder_24h_sent = True
                locked.save(update_fields=['reminder_24h_sent'])
                sent_24h += 1
        except Interview.DoesNotExist:
            continue

    logger.info(f"Sent {sent_24h} 24-hour reminders")

    # 1-hour reminders
    interviews_1h = Interview.objects.needing_1h_reminder()
    sent_1h = 0
    for interview in interviews_1h:
        try:
            with transaction.atomic():
                locked = Interview.objects.select_for_update().get(pk=interview.pk)
                if locked.reminder_1h_sent:
                    continue
                _send_reminder_email(locked, "1 hour")
                locked.reminder_1h_sent = True
                locked.save(update_fields=['reminder_1h_sent'])
                sent_1h += 1
        except Interview.DoesNotExist:
            continue

    logger.info(f"Sent {sent_1h} 1-hour reminders")


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_interview_cancellation(self, interview_id):
    """
    Send interview cancellation email
    
    Args:
        interview_id: UUID of the cancelled interview
    """
    try:
        interview = Interview.objects.select_related(
            'application__applicant',
            'application__applicant__personalprofile',
            'application__job__company',
            'cancelled_by'
        ).get(id=interview_id)
    except Interview.DoesNotExist:
        logger.error(f"Interview {interview_id} not found for cancellation email")
        return
    
    candidate = interview.application.applicant
    
    # Get candidate name
    try:
        candidate_name = candidate.personalprofile.full_name
    except:
        candidate_name = candidate.email
    
    context = {
        'interview': interview,
        'candidate': candidate,
        'candidate_name': candidate_name,
    }
    
    subject = f"Interview Cancelled: {interview.application.job.title}"
    
    try:
        html_message = render_to_string('interviews/emails/cancellation.html', context)
        text_message = render_to_string('interviews/emails/cancellation.txt', context)
    except Exception as e:
        logger.error(f"Failed to render cancellation email template: {e}")
        raise self.retry(exc=e)
    
    # Send to candidate
    recipients = [candidate.email]
    
    # Add interviewer if applicable
    if interview.interviewer_email:
        recipients.append(interview.interviewer_email)
    
    try:
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)
        
        logger.info(f"Cancellation email sent for interview {interview_id}")
    except Exception as e:
        logger.error(f"Failed to send cancellation email: {e}")
        raise self.retry(exc=e)


@shared_task
def cleanup_old_interviews():
    """
    Archive or cleanup very old completed/cancelled interviews
    Runs monthly via Celery Beat
    """
    cutoff_date = timezone.now() - timedelta(days=365)  # 1 year ago
    
    old_interviews = Interview.objects.filter(
        scheduled_date__lt=cutoff_date,
        status__in=[Interview.InterviewStatus.COMPLETED, Interview.InterviewStatus.CANCELLED]
    )
    
    count = old_interviews.count()
    
    # In production, you might want to archive to a separate table
    # For now, we'll just log
    logger.info(f"Found {count} interviews older than 1 year")
    
    # Optionally delete very old cancelled interviews
    # old_cancelled = old_interviews.filter(status=Interview.InterviewStatus.CANCELLED)
    # deleted = old_cancelled.delete()
    # logger.info(f"Deleted {deleted[0]} old cancelled interviews")


@shared_task
def send_post_interview_followup(interview_id):
    """
    Send follow-up email after interview completion
    
    Args:
        interview_id: UUID of the completed interview
    """
    try:
        interview = Interview.objects.select_related(
            'application__applicant',
            'application__applicant__personalprofile',
            'application__job__company'
        ).get(id=interview_id)
    except Interview.DoesNotExist:
        logger.error(f"Interview {interview_id} not found for follow-up email")
        return
    
    # Only send if interview is completed
    if interview.status != Interview.InterviewStatus.COMPLETED:
        return
    
    candidate = interview.application.applicant
    
    # Get candidate name
    try:
        candidate_name = candidate.personalprofile.full_name
    except:
        candidate_name = candidate.email
    
    context = {
        'interview': interview,
        'candidate': candidate,
        'candidate_name': candidate_name,
    }
    
    subject = f"Thank you for interviewing with {interview.application.job.company.company_name}"
    
    try:
        html_message = render_to_string('interviews/emails/followup.html', context)
        
        send_mail(
            subject=subject,
            message='',
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[candidate.email],
            fail_silently=True,
        )
        
        logger.info(f"Follow-up email sent for interview {interview_id}")
    except Exception as e:
        logger.error(f"Failed to send follow-up email: {e}")
