"""
Celery tasks for screening system - processing resumes, calculating match scores,
updating session statistics, sending notifications, and cleaning up old files.
"""
import logging
from celery import shared_task
from django.core.files.storage import default_storage
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_resume_screening(self, result_id, file_path=None):
    """Process or re-process a single screening result.

    This task supports both the new application-linked flow and the legacy resume-only flow.

    Args:
        result_id (UUID): ScreeningResult identifier.

    Raises:
        Exception: Propagated after marking the result failed to avoid silent drops.
    """
    result = None
    try:
        from .models import ScreeningResult, ScreeningResultStatus
        from .ai_matcher import ai_screener
        from .services import ApplicationDataService
        from apps.resumes.parsers import ResumeParser

        try:
            result = ScreeningResult.objects.select_related(
                'session',
                'session__criteria',
                'job',
                'application__applicant'
            ).get(id=result_id)
        except ScreeningResult.DoesNotExist:
            logger.error(f"ScreeningResult {result_id} does not exist")
            return f"Failed: ScreeningResult {result_id} not found"

        result.mark_as_processing()

        resume_text = ''
        application_data = None
        if result.application:
            # Application-based screening path: enrich candidates with stored data.
            logger.info(f"Screening application {result.application.id} for job {result.job.title if result.job else 'General'}")
            application_data = ApplicationDataService.get_application_screening_data(result.application)
            resume_text = application_data.get('resume_text') or ''
        else:
            # Legacy resume-only path: parse the uploaded file for text extraction.
            source_file_path = file_path or result.file_path or (result.resume.file.name if result.resume and result.resume.file else None)
            if not source_file_path:
                error_msg = "No resume file attached"
                logger.error(error_msg)
                result.mark_as_failed(error_msg)
                raise Exception(error_msg)
            try:
                with default_storage.open(source_file_path, 'rb') as file:
                    file_content = file.read()
                filename = source_file_path.split('/')[-1]
                parser = ResumeParser()
                parsed_result = parser.parse_content(file_content, filename)

                if not parsed_result.get('success'):
                    error_msg = parsed_result.get('error', 'Unknown parsing error')
                    logger.error(f"Resume parsing failed for {filename}: {error_msg}")
                    result.mark_as_failed(f"Failed to parse resume: {error_msg}")
                    raise Exception(error_msg)

                resume_text = parsed_result.get('text', '')
                if not resume_text or len(resume_text.strip()) < 50:
                    error_msg = "Insufficient text extracted from resume"
                    logger.error(f"{error_msg} for {filename}")
                    result.mark_as_failed(error_msg)
                    raise Exception(error_msg)
            except Exception as e:
                logger.error(f"Error parsing resume for result {result_id}: {e}", exc_info=True)
                if not getattr(result, 'status', None) == ScreeningResultStatus.FAILED:
                    result.mark_as_failed(f"Failed to parse resume: {str(e)}")
                # Re-raise so Celery can record the failure for retries.
                raise

        if not resume_text:
            error_msg = "Unable to obtain resume text"
            logger.error(error_msg)
            result.mark_as_failed(error_msg)
            raise Exception(error_msg)

        job_description = result.job.description if result.job else "General screening results"
        criteria = result.session.criteria
        criteria_dict = {
            'required_skills': criteria.required_skills,
            'nice_to_have_skills': criteria.nice_to_have_skills,
            'min_experience_years': criteria.min_experience_years,
            'max_experience_years': criteria.max_experience_years,
            'required_education': criteria.required_education,
            'custom_keywords': criteria.custom_keywords,
            'weight_skills': criteria.weight_skills,
            'weight_experience': criteria.weight_experience,
            'weight_education': criteria.weight_education,
            'weight_keywords': criteria.weight_keywords,
            'weight_screening_questions': criteria.weight_screening_questions,
            'weight_assessments': criteria.weight_assessments,
            'screening_questions_config': criteria.screening_questions_config
        }

        if application_data:
            candidate_name = application_data['candidate_info']['name']
            logger.info(f"Screening application {result.application.id} for job {result.job.title if result.job else 'General'} (Candidate: {candidate_name})")
            try:
                match_result = ai_screener.calculate_match_score(
                    resume_text=resume_text,
                    job_description=job_description,
                    criteria=criteria_dict,
                    application_data=application_data
                )

                result.match_score = match_result['match_score']
                result.match_details = match_result['match_details']
                result.screening_answers = application_data.get('screening_answers', [])
                result.assessment_data = application_data.get('assessment_results', [])
                result.save(update_fields=[
                    'match_score', 'match_details', 'screening_answers', 'assessment_data'
                ])
                logger.info(f"Candidate: {candidate_name}, Match Score: {result.match_score}%")
            except Exception as e:
                logger.error(f"Error calculating match score: {e}", exc_info=True)
                result.mark_as_failed(f"Failed to calculate match: {str(e)}")
                raise
        else:
            logger.info(f"Screening result {result_id} for job {result.job.title if result.job else 'General'} (no application link)")
            try:
                match_result = ai_screener.calculate_match_score(
                    resume_text=resume_text,
                    job_description=job_description,
                    criteria=criteria_dict
                )

                result.match_score = match_result['match_score']
                result.match_details = match_result['match_details']
                result.save(update_fields=['match_score', 'match_details'])
                logger.info(f"Match score calculated: {result.match_score}%")
            except Exception as e:
                logger.error(f"Error calculating match score: {e}", exc_info=True)
                result.mark_as_failed(f"Failed to calculate match: {str(e)}")
                raise

        # Mark as completed
        result.mark_as_completed()
        
        # Send result update via WebSocket
        try:
            from .websocket_service import WebSocketService
            import asyncio
            
            result_data = {
                'id': str(result.id),
                'candidate_name': result.candidate_name,
                'match_score': result.match_score,
                'status': result.status,
                'skills_match': result.skills_match,
                'experience_match': result.experience_match,
                'education_match': result.education_match,
            }
            
            # Send WebSocket update (run in thread pool)
            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                WebSocketService.send_result_update(result.session.id, result_data)
            )
            loop.close()
            logger.info(f"Sent WebSocket update for result {result_id}")
        except Exception as e:
            logger.warning(f"Failed to send WebSocket update: {e}")
        
        # Update session statistics
        try:
            with transaction.atomic():
                session = result.session
                session.processed_resumes += 1
                
                # Update average score
                from django.db.models import Avg
                avg_score = session.results.filter(
                    status=ScreeningResultStatus.COMPLETED
                ).aggregate(avg=Avg('match_score'))['avg']
                
                session.average_match_score = avg_score
                
                # Check if all done
                if session.processed_resumes + session.failed_resumes >= session.total_resumes:
                    session.mark_completed()
                    logger.info(f"Session {session.id} completed")
                
                session.save()
                logger.info(f"Session statistics updated for {session.id}")
        except Exception as e:
            logger.error(f"Error updating session statistics: {e}", exc_info=True)
            # Don't fail the task for stats update issues
        
        logger.info(f"Resume screening completed successfully for result {result_id}")
        return f"Successfully processed result {result_id}"
        
    except Exception as exc:
        logger.error(f"Error in resume screening task: {str(exc)}", exc_info=True)
        
        # Retry with exponential backoff
        try:
            retry_countdown = 60 * (2 ** self.request.retries)
            logger.info(f"Retrying in {retry_countdown} seconds (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=exc, countdown=retry_countdown)
        except self.MaxRetriesExceededError:
            # Mark as failed after all retries
            logger.error(f"Max retries exceeded for result {result_id}")
            try:
                if result:
                    result.mark_as_failed(f"Max retries exceeded: {str(exc)}")
                else:
                    # Try to get result one more time
                    from .models import ScreeningResult
                    result = ScreeningResult.objects.get(id=result_id)
                    result.mark_as_failed(f"Max retries exceeded: {str(exc)}")
                
                # Update session
                with transaction.atomic():
                    session = result.session
                    session.failed_resumes += 1
                    
                    # Check if all done
                    if session.processed_resumes + session.failed_resumes >= session.total_resumes:
                        session.mark_completed()
                    
                    session.save()
            except Exception as e:
                logger.error(f"Error updating failed result: {e}", exc_info=True)
            
            return f"Failed to process result {result_id} after {self.max_retries} retries"


@shared_task(bind=True)
def process_screening_session(self, session_id):
    """
    Process all resumes in a screening session.
    
    Args:
        session_id: UUID of ScreeningSession
    """
    try:
        from .models import ScreeningSession, ScreeningStatus
        
        session = ScreeningSession.objects.get(id=session_id)
        session.start_processing()
        
        # Get all pending results
        pending_results = session.results.filter(status='pending')
        
        logger.info(f"Processing {pending_results.count()} resumes for session {session_id}")
        
        # Queue each result for processing
        for result in pending_results:
            process_resume_screening.delay(result.id)
        
        return f"Queued {pending_results.count()} resumes for processing"
        
    except Exception as exc:
        logger.error(f"Error processing screening session: {str(exc)}", exc_info=True)
        
        try:
            session = ScreeningSession.objects.get(id=session_id)
            session.mark_failed()
        except Exception as e:
            logger.error(f"Error marking session as failed: {e}")
        
        return f"Failed to process session {session_id}"


@shared_task
def update_session_statistics(session_id):
    """
    Update session statistics.
    
    Args:
        session_id: UUID of ScreeningSession
    """
    try:
        from .models import ScreeningSession
        
        session = ScreeningSession.objects.get(id=session_id)
        session.update_statistics()
        
        logger.info(f"Statistics updated for session {session_id}")
        return f"Statistics updated for session {session_id}"
        
    except Exception as exc:
        logger.error(f"Error updating statistics: {str(exc)}", exc_info=True)
        return f"Failed to update statistics for session {session_id}"


@shared_task(bind=True, max_retries=3)
def send_screening_complete_notification(self, session_id):
    """
    Send notification when screening is complete.
    
    Args:
        session_id: UUID of ScreeningSession
    """
    try:
        from .models import ScreeningSession
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        session = ScreeningSession.objects.select_related(
            'company',
            'company__user',
            'job'
        ).get(id=session_id)
        
        # Get statistics
        total = session.total_resumes
        processed = session.processed_resumes
        avg_score = session.average_match_score or 0
        high_matches = session.results.filter(match_score__gte=80).count()
        
        # Render email
        subject = f"Screening Complete - {session.title}"
        
        html_message = render_to_string('screening/emails/screening_complete.html', {
            'company_name': session.company.company_name,
            'session_title': session.title,
            'job_title': session.job.title if session.job else 'General Screening',
            'total_resumes': total,
            'processed': processed,
            'average_score': avg_score,
            'high_matches': high_matches,
            'session_url': f"/screening/sessions/{session.id}/results/",
        })
        
        # Send email
        send_mail(
            subject=subject,
            message=f"Your screening session '{session.title}' is complete!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[session.company.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Screening complete notification sent for session {session_id}")
        return f"Notification sent for session {session_id}"
        
    except Exception as exc:
        logger.error(f"Error sending notification: {str(exc)}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)


@shared_task
def cleanup_old_screening_files():
    """
    Periodic task to clean up old screening files.
    
    Runs weekly to delete files from completed sessions older than 30 days.
    """
    try:
        from .models import ScreeningSession, ScreeningStatus
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=30)
        
        old_sessions = ScreeningSession.objects.filter(
            status__in=[ScreeningStatus.COMPLETED, ScreeningStatus.FAILED],
            completed_at__lt=cutoff_date
        )
        
        deleted_count = 0
        for session in old_sessions:
            try:
                # Delete files
                folder_path = f'screening_resumes/{session.id}/'
                
                # List and delete files
                dirs, files = default_storage.listdir(folder_path)
                for file in files:
                    file_path = f"{folder_path}{file}"
                    default_storage.delete(file_path)
                    deleted_count += 1
                
                logger.info(f"Deleted {len(files)} files from session {session.id}")
            except Exception as e:
                logger.error(f"Error cleaning up session {session.id}: {e}")
        
        logger.info(f"Cleaned up {deleted_count} old screening files")
        return f"Deleted {deleted_count} files"
        
    except Exception as exc:
        logger.error(f"Error in cleanup task: {str(exc)}", exc_info=True)
        return f"Error: {str(exc)}"


@shared_task
def generate_screening_report(session_id, export_format='excel'):
    """
    Generate screening report asynchronously.
    
    Args:
        session_id: UUID of ScreeningSession
        export_format: 'csv', 'excel', or 'pdf'
    """
    try:
        from .models import ScreeningSession
        
        session = ScreeningSession.objects.get(id=session_id)
        
        # This would generate the report and store it
        # For now, log the action
        logger.info(f"Generating {export_format} report for session {session_id}")
        
        return f"Report generated for session {session_id}"
        
    except Exception as exc:
        logger.error(f"Error generating report: {str(exc)}", exc_info=True)
        return f"Failed to generate report for session {session_id}"


@shared_task(bind=True, max_retries=2)
def generate_interview_questions_async(self, session_id, result_id):
    """
    Generate interview questions for a candidate asynchronously.
    
    Args:
        session_id: UUID of ScreeningSession
        result_id: UUID of ScreeningResult
    """
    try:
        from .models import ScreeningSession, ScreeningResult
        from .mistral_client import mistral_client
        
        session = ScreeningSession.objects.select_related('job', 'criteria').get(id=session_id)
        result = ScreeningResult.objects.get(id=result_id)
        
        if not mistral_client.is_available():
            logger.warning("Mistral AI not available for question generation")
            return "Mistral AI not available"
        
        # Get criteria
        criteria = session.criteria
        
        # Generate questions
        questions = mistral_client.generate_interview_questions(
            job_title=session.job.title if session.job else "General Position",
            required_skills=criteria.required_skills,
            experience_level="senior",  # Could be dynamic
            num_questions=10
        )
        
        # Store in result match_details
        result.match_details['interview_questions'] = questions
        result.save()
        
        logger.info(f"Interview questions generated for result {result_id}")
        return f"Generated {len(questions)} questions"
        
    except Exception as exc:
        logger.error(f"Error generating interview questions: {str(exc)}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)


@shared_task
def generate_candidate_summary_async(result_id):
    """
    Generate candidate executive summary asynchronously.
    
    Args:
        result_id: UUID of ScreeningResult
    """
    try:
        from .models import ScreeningResult
        from .mistral_client import mistral_client
        from apps.resumes.parsers import ResumeParser
        
        result = ScreeningResult.objects.select_related('resume', 'session').get(id=result_id)
        
        if not mistral_client.is_available():
            logger.warning("Mistral AI not available for summary generation")
            return "Mistral AI not available"
        
        # Get resume text
        parser = ResumeParser()
        resume_text = parser.get_resume_text(result.resume)
        
        # Get strengths and weaknesses from match details
        match_details = result.match_details
        strengths = match_details.get('strengths', [])
        weaknesses = match_details.get('weaknesses', [])
        
        # Generate summary
        summary = mistral_client.generate_candidate_summary(
            resume_text=resume_text,
            match_score=result.match_score,
            strengths=strengths,
            weaknesses=weaknesses
        )
        
        # Store in match_details
        result.match_details['executive_summary'] = summary
        result.save()
        
        logger.info(f"Candidate summary generated for result {result_id}")
        return "Summary generated"
        
    except Exception as exc:
        logger.error(f"Error generating candidate summary: {str(exc)}", exc_info=True)
        return f"Error: {str(exc)}"


@shared_task
def detect_bias_async(session_id):
    """
    Detect bias in job description and criteria asynchronously.
    
    Args:
        session_id: UUID of ScreeningSession
    """
    try:
        from .models import ScreeningSession
        from .mistral_client import mistral_client
        
        session = ScreeningSession.objects.select_related('job', 'criteria').get(id=session_id)
        
        if not mistral_client.is_available():
            logger.warning("Mistral AI not available for bias detection")
            return "Mistral AI not available"
        
        # Get job description
        if session.job:
            job_description = session.job.description
        else:
            job_description = "General screening"
        
        # Get criteria
        criteria = session.criteria
        criteria_dict = {
            'required_skills': criteria.required_skills,
            'min_experience_years': criteria.min_experience_years,
            'required_education': criteria.required_education,
        }
        
        # Detect bias
        bias_analysis = mistral_client.detect_bias(
            job_description=job_description,
            screening_criteria=criteria_dict
        )
        
        # Store in session settings
        settings = session.settings or {}
        settings['bias_analysis'] = bias_analysis
        settings['bias_checked_at'] = timezone.now().isoformat()
        session.settings = settings
        session.save()
        
        logger.info(f"Bias analysis completed for session {session_id}")
        return f"Bias score: {bias_analysis.get('bias_score', 0)}"
        
    except Exception as exc:
        logger.error(f"Error detecting bias: {str(exc)}", exc_info=True)
        return f"Error: {str(exc)}"
