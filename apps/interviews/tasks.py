from datetime import timedelta
from io import BytesIO
from django.db import models, transaction
from django.template.loader import render_to_string
from django.core.mail import EmailMessage, send_mail
from django.utils import timezone
from django.conf import settings
from celery import shared_task
import logging
try:
    import sentry_sdk
except Exception:
    sentry_sdk = None

from apps.notifications.emails import (
    send_practice_ready_email,
    send_report_ready_email,
    send_milestone_email,
)

from .models import (
    Interview,
    ArchivedInterview,
    InterviewPracticeSession,
    PracticeQuestion,
    PracticeResponse,
    PracticePerformanceReport,
    PracticeMilestoneLog,
)
from .ai import (
    generate_questions as ai_generate_questions,
    score_response as ai_score_response,
    summarize_session as ai_summarize_session
)
from .ai_connector import QuestionValidator, ValidationError, ResponseScorer, AIConnector
from . import progress_tasks  # Import for real-time progress tracking
from django.urls import reverse

from apps.notifications.signals import notification_create
from apps.notifications.models import NotificationType

logger = logging.getLogger(__name__)
MILESTONE_SESSION_COUNTS = (5,)


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


def _check_practice_milestones(session):
    """Send milestone rewards when candidates hit practice counts."""
    user = session.candidate
    if not user:
        return

    completed_count = InterviewPracticeSession.objects.filter(
        candidate=user,
        status=InterviewPracticeSession.Status.COMPLETED
    ).count()

    for milestone in MILESTONE_SESSION_COUNTS:
        if completed_count >= milestone:
            already_created = PracticeMilestoneLog.objects.filter(
                user=user,
                milestone=milestone
            ).exists()
            if already_created:
                continue

            try:
                send_milestone_email(user, milestone)
            except Exception as exc:
                logger.warning("Failed to send milestone email for user %s: %s", user.id, exc)
            PracticeMilestoneLog.objects.create(user=user, milestone=milestone)


@shared_task
def generate_video_thumbnail(storage_path):
    """Generate a small JPEG thumbnail from an uploaded video if ffmpeg is available.

    Args:
        storage_path: path in storage (relative) where video was saved
    """
    try:
        from django.core.files.storage import default_storage
        import subprocess
        import os

        local_tmp = default_storage.path(storage_path)
        thumb_name = os.path.splitext(storage_path)[0] + '_thumb.jpg'
        local_thumb = default_storage.path(thumb_name)

        # Try to extract first frame using ffmpeg
        cmd = ['ffmpeg', '-y', '-i', local_tmp, '-ss', '00:00:00.500', '-vframes', '1', local_thumb]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Ensure thumbnail is saved by storage (if not local)
        if not default_storage.exists(thumb_name):
            with open(local_thumb, 'rb') as f:
                default_storage.save(thumb_name, f)
    except Exception as exc:
        logger.debug('Thumbnail generation failed: %s', exc)
        if sentry_sdk:
            sentry_sdk.capture_exception(exc)
        return


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
    retention_days = getattr(settings, 'INTERVIEW_RETENTION_DAYS', 365)
    cutoff_date = timezone.now() - timedelta(days=retention_days)

    old_interviews = Interview.objects.filter(
        scheduled_date__lt=cutoff_date,
        status__in=[Interview.InterviewStatus.COMPLETED, Interview.InterviewStatus.CANCELLED]
    )

    archived_count = 0
    archived_ids = []

    for interview in old_interviews:
        company_user = getattr(interview.application.job.company, 'user', None)
        ArchivedInterview.objects.update_or_create(
            interview_id=interview.id,
            defaults={
                'application': interview.application,
                'company': company_user,
                'job_title': interview.application.job.title,
                'applicant_email': interview.application.applicant.email,
                'status': interview.status,
                'scheduled_date': interview.scheduled_date,
                'payload': interview.to_archive_payload(),
            }
        )
        archived_count += 1
        archived_ids.append(interview.id)

    deleted_rows = 0
    if archived_ids:
        deleted_rows, _ = Interview.objects.filter(id__in=archived_ids).delete()

    logger.info(
        f"Archived {archived_count} old interviews ({retention_days}-day retention); "
        f"deleted {deleted_rows} records."
    )


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


@shared_task
def generate_practice_questions(session_id):
    """Generate practice questions via the AI connector with validation."""
    try:
        session = InterviewPracticeSession.objects.get(id=session_id)
    except InterviewPracticeSession.DoesNotExist:
        logger.error(f"Practice session {session_id} not found")
        return

    logger.info("Generating practice questions for session %s", session_id)
    session.question_generation_state = InterviewPracticeSession.GenerationState.IN_PROGRESS
    session.save(update_fields=['question_generation_state'])
    
    # Broadcast: Starting generation
    progress_tasks.track_question_generation_progress.delay(
        str(session_id),
        {
            'stage': 'initializing',
            'message': 'Initializing question generation...',
            'progress': 5,
            'timestamp': timezone.now().isoformat()
        }
    )

    # Generate questions from AI
    progress_tasks.track_question_generation_progress.delay(
        str(session_id),
        {
            'stage': 'generating',
            'message': f'Generating AI interview questions for {session.settings.get("role_title", "role")}...',
            'progress': 30,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    questions, raw_response, model_used = ai_generate_questions(session)
    
    # Store raw response for debugging
    if not session.settings:
        session.settings = {}
    session.settings['raw_ai_response'] = raw_response[:1000] if raw_response else None  # Limit size
    session.settings['ai_model_used'] = model_used
    
    if not questions:
        error_msg = "Failed to generate AI questions. All AI services exhausted or unavailable."
        logger.error(f"Question generation failed for session {session_id}: {error_msg}")
        
        # Mark session as FAILED and store error message
        session.status = InterviewPracticeSession.Status.FAILED
        session.question_generation_state = InterviewPracticeSession.GenerationState.FAILED
        session.settings['error_message'] = error_msg
        session.settings['error_raw_response'] = raw_response[:1000] if raw_response else None
        session.save(update_fields=['status', 'question_generation_state', 'settings'])
        
        # Broadcast: Generation failed
        progress_tasks.broadcast_session_update.delay(
            str(session_id),
            'generation_failed',
            {'error': error_msg, 'timestamp': timezone.now().isoformat()}
        )
        return
    
    # Broadcast: Validating questions
    progress_tasks.track_question_generation_progress.delay(
        str(session_id),
        {
            'stage': 'validating',
            'message': f'Validating {len(questions)} questions...',
            'progress': 60,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    # Validate questions
    try:
        # Parse raw response to validate
        import json
        parsed = json.loads(raw_response)
        validated_questions = QuestionValidator.validate(parsed)
        logger.info(f"Successfully validated {len(validated_questions)} questions for session {session_id}")
    except (ValidationError, json.JSONDecodeError, TypeError) as e:
        logger.error(
            f"Question validation failed for session {session_id}: {e}. "
            f"Raw response: {raw_response[:200]}..."
        )
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        error_msg = f"Question validation failed: {str(e)}"
        
        # Mark session as FAILED
        session.status = InterviewPracticeSession.Status.FAILED
        session.question_generation_state = InterviewPracticeSession.GenerationState.FAILED
        session.settings['error_message'] = error_msg
        session.settings['validation_error'] = str(e)
        session.save(update_fields=['status', 'question_generation_state', 'settings'])
        
        # Broadcast: Validation failed
        progress_tasks.broadcast_session_update.delay(
            str(session_id),
            'validation_failed',
            {'error': error_msg, 'timestamp': timezone.now().isoformat()}
        )
        return
    
    # Broadcast: Saving questions
    progress_tasks.track_question_generation_progress.delay(
        str(session_id),
        {
            'stage': 'saving',
            'message': 'Saving questions to database...',
            'progress': 80,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    # Create PracticeQuestion objects
    for idx, data in enumerate(validated_questions, start=1):
        PracticeQuestion.objects.create(
            session=session,
            prompt=data.get('prompt', f'Practice question #{idx}'),
            category=data.get('category', 'behavioral'),
            difficulty=data.get('difficulty', 'medium'),
            evaluation_criteria=data.get('evaluation_criteria', []),
            order=data.get('order', idx),
            ai_request_id=data.get('request_id', '')
        )

    session.status = InterviewPracticeSession.Status.IN_PROGRESS
    session.question_generation_state = InterviewPracticeSession.GenerationState.COMPLETED
    session.save(update_fields=['status', 'question_generation_state', 'settings'])
    
    try:
        send_practice_ready_email(session)
    except Exception as exc:
        logger.warning(
            "Failed to send practice ready email for session %s: %s",
            session_id,
            exc
        )

    # Broadcast: Generation complete
    progress_tasks.broadcast_session_update.delay(
        str(session_id),
        'generation_complete',
        {
            'questions_count': len(validated_questions),
            'ai_model': model_used,
            'timestamp': timezone.now().isoformat()
        }
    )


@shared_task
def analyze_practice_response(response_id):
    """Score a candidate response using comprehensive AI-powered analysis."""
    try:
        response = PracticeResponse.objects.select_related(
            'session__candidate',
            'question__session__candidate'
        ).get(id=response_id)
    except PracticeResponse.DoesNotExist:
        logger.error(f"Practice response {response_id} not found")
        return

    logger.info("Scoring practice response %s", response_id)
    response.analysis_status = InterviewPracticeSession.GenerationState.IN_PROGRESS
    response.save(update_fields=['analysis_status'])

    try:
        # Initialize AI connector for scoring
        ai_connector = AIConnector()
        
        # Prepare evaluation criteria
        evaluation_criteria = response.question.evaluation_criteria or []
        if isinstance(evaluation_criteria, dict):
            evaluation_criteria = list(evaluation_criteria.keys())
        
        # Extract video metrics if available
        video_metrics = None
        if response.video_analysis_metrics:
            video_metrics = response.video_analysis_metrics.get('summary', {})
        
        # Score the response
        scoring_result, raw_response, model_used = ai_connector.score_response(
            question_prompt=response.question.prompt,
            answer_text=response.text_response,
            evaluation_criteria=evaluation_criteria,
            video_metrics=video_metrics
        )
        
        # Store AI model information
        response.ai_scoring_model = model_used or 'unknown'
        response.analysis_request_id = scoring_result.get('request_id', '')
        
        # Check if scoring was successful
        if not scoring_result.get('success'):
            error_msg = scoring_result.get('error', 'Unknown scoring error')
            logger.error(f"Scoring failed for response {response_id}: {error_msg}")
            response.analysis_status = InterviewPracticeSession.GenerationState.FAILED
            response.analysis = {
                'error': error_msg,
                'raw_response': raw_response[:500] if raw_response else None
            }
            response.save(update_fields=[
                'analysis_status',
                'analysis',
                'analysis_request_id',
                'ai_scoring_model'
            ])
            # Notify candidate about failed scoring attempt (in-app)
            try:
                link = reverse('interviews:practice_response_analysis', kwargs={'response_id': response.id})
                notification_create.send(
                    sender=analyze_practice_response,
                    user=response.session.candidate,
                    title="We couldn't score one of your responses",
                    message=f"There was a problem scoring your response to '{response.question.prompt[:80]}'. Our team has been notified.",
                    link=link,
                    notification_type=NotificationType.SYSTEM,
                    action_text='View response'
                )
            except Exception:
                logger.debug('Failed to create in-app notification for failed scoring %s', response.id)
        else:
            # Store scores
            response.content_score = scoring_result.get('content_score', 0)
            response.delivery_score = scoring_result.get('delivery_score', 0)
            response.presence_score = scoring_result.get('presence_score', 0)
            response.ai_score = scoring_result.get('overall_score', 0)
            
            # Store strengths and improvements
            response.strengths = scoring_result.get('strengths', [])
            response.improvements = scoring_result.get('improvements', [])
            
            # Store feedback
            feedback_list = scoring_result.get('feedback', [])
            response.ai_feedback = '\n'.join(feedback_list) if feedback_list else ''
            
            # Store detailed analysis
            response.analysis = {
                'overall_feedback': scoring_result.get('overall_feedback', ''),
                'key_points_covered': scoring_result.get('key_points_covered', []),
                'feedback_points': feedback_list,
                'model_used': model_used
            }
            
            response.analysis_status = InterviewPracticeSession.GenerationState.COMPLETED
            
            logger.info(
                f"Response {response_id} scored successfully - "
                f"Overall: {response.ai_score}, Content: {response.content_score}, "
                f"Delivery: {response.delivery_score}, Presence: {response.presence_score}"
            )
            
            response.save(update_fields=[
                'content_score',
                'delivery_score',
                'presence_score',
                'ai_score',
                'ai_feedback',
                'analysis',
                'analysis_status',
                'analysis_request_id',
                'strengths',
                'improvements',
                'ai_scoring_model'
            ])
            # Notify candidate about scored response (in-app)
            try:
                link = reverse('interviews:practice_response_analysis', kwargs={'response_id': response.id})
                notification_create.send(
                    sender=analyze_practice_response,
                    user=response.session.candidate,
                    title="Your practice response has been scored",
                    message=f"Your response to '{response.question.prompt[:80]}' has been scored. Tap to view feedback.",
                    link=link,
                    notification_type=NotificationType.SYSTEM,
                    action_text='View feedback'
                )
            except Exception:
                logger.debug('Failed to create in-app notification for scored response %s', response.id)
    
    except Exception as exc:
        logger.error(f"Exception during response scoring: {exc}", exc_info=True)
        if sentry_sdk:
            sentry_sdk.capture_exception(exc)
        response.analysis_status = InterviewPracticeSession.GenerationState.FAILED
        response.analysis = {'error': str(exc)}
        response.save(update_fields=['analysis_status', 'analysis'])
        return

    # Check if all responses in the session are analyzed
    session = response.session or response.question.session
    incomplete = PracticeResponse.objects.filter(
        session=session
    ).exclude(
        analysis_status=InterviewPracticeSession.GenerationState.COMPLETED
    ).exists()

    if not incomplete:
        generate_practice_report.delay(session.id)


@shared_task
def generate_practice_report(session_id):
    """Generate a summary report from all scored responses."""
    try:
        session = InterviewPracticeSession.objects.prefetch_related('questions__responses').get(id=session_id)
    except InterviewPracticeSession.DoesNotExist:
        logger.error(f"Practice session {session_id} not found")
        return
    try:
        logger.info("Generating practice report for session %s", session_id)
        session.report_generation_state = InterviewPracticeSession.GenerationState.IN_PROGRESS
        session.save(update_fields=['report_generation_state'])

        report_data = ai_summarize_session(session)
        overall = report_data.get('overall_score')
        if overall is None:
            aggregate = session.questions.aggregate(models.Avg('responses__ai_score'))
            overall = aggregate.get('responses__ai_score__avg') or 0

        report, _ = PracticePerformanceReport.objects.update_or_create(
            session=session,
            defaults={
                'overall_score': overall,
                'strengths': report_data.get('strengths', []),
                'weaknesses': report_data.get('weaknesses', []),
                'recommendations': report_data.get('recommendations', ''),
                'ai_request_id': report_data.get('request_id', '')
            }
        )

        session.overall_score = overall
        session.status = InterviewPracticeSession.Status.COMPLETED
        session.completed_at = timezone.now()
        session.report_generation_state = InterviewPracticeSession.GenerationState.COMPLETED
        session.save(update_fields=[
            'overall_score',
            'status',
            'completed_at',
            'report_generation_state'
        ])

        # Send email notification (existing)
        try:
            send_report_ready_email(session)
        except Exception as exc:
            logger.warning(
                "Failed to send practice report email for session %s: %s",
                session_id,
                exc
            )
            if sentry_sdk:
                sentry_sdk.capture_exception(exc)

        # In-app notification: report ready
        try:
            link = reverse('interviews:practice_report', kwargs={'session_id': session.id})
            notification_create.send(
                sender=generate_practice_report,
                user=session.candidate,
                title="Your interview performance report is ready",
                message=f"Your practice session score: {overall}. Tap to view detailed feedback.",
                link=link,
                notification_type=NotificationType.SYSTEM,
                action_text='View report'
            )
        except Exception:
            logger.debug('Failed to create in-app notification for report %s', session.id)

        _check_practice_milestones(session)
    except Exception as exc:
        logger.error(f"Exception generating practice report for session {session_id}: {exc}", exc_info=True)
        if sentry_sdk:
            sentry_sdk.capture_exception(exc)
        # Attempt to notify the user that report generation failed
        try:
            if session and getattr(session, 'candidate', None):
                notification_create.send(
                    sender=generate_practice_report,
                    user=session.candidate,
                    title="We couldn't generate your practice report",
                    message="There was an error generating your report. Please try again or contact support.",
                    link=reverse('interviews:practice_dashboard'),
                    notification_type=NotificationType.SYSTEM,
                    action_text='View dashboard'
                )
        except Exception:
            logger.debug('Failed to create failure notification for report %s', session_id)
        return
