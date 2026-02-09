"""
Celery tasks for asynchronous resume parsing.

To use:
1. Install Celery: pip install celery redis
2. Configure Celery in settings.py
3. Run worker: celery -A hiresight worker -l info
4. Call in views: parse_resume_async.delay(resume.pk)
"""

from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry after 60 seconds
)
def parse_resume_async(self, resume_id):
    """
    Parse resume asynchronously.
    
    Args:
        resume_id: ID of the Resume object to parse
        
    Returns:
        dict: Parsing result
    """
    from .models import Resume
    from .parsers import resume_parser
    
    try:
        # Get resume
        resume = Resume.objects.get(pk=resume_id)
        
        # Mark as parsing
        resume.mark_as_parsing()
        
        # Parse the resume
        result = resume_parser.parse_file(
            resume.file.path,
            resume.original_filename
        )
        
        if result.get('success'):
            resume.mark_as_parsed(result)
            logger.info(f"Successfully parsed resume {resume_id}")
            return {
                'success': True,
                'resume_id': resume_id,
                'skills_count': len(result.get('skills', [])),
            }
        else:
            error_msg = result.get('error', 'Unknown parsing error')
            resume.mark_as_failed(error_msg)
            logger.error(f"Failed to parse resume {resume_id}: {error_msg}")
            return {
                'success': False,
                'resume_id': resume_id,
                'error': error_msg,
            }
    
    except Resume.DoesNotExist:
        logger.error(f"Resume {resume_id} not found")
        return {
            'success': False,
            'resume_id': resume_id,
            'error': 'Resume not found',
        }
    
    except Exception as e:
        logger.error(f"Error parsing resume {resume_id}: {str(e)}", exc_info=True)
        
        # Retry the task
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            # Max retries reached, mark as failed
            try:
                resume = Resume.objects.get(pk=resume_id)
                resume.mark_as_failed(f"Max retries exceeded: {str(e)}")
            except:
                pass
            
            return {
                'success': False,
                'resume_id': resume_id,
                'error': f'Max retries exceeded: {str(e)}',
            }


@shared_task
def batch_parse_resumes(resume_ids):
    """
    Parse multiple resumes in batch.
    
    Args:
        resume_ids: List of resume IDs to parse
        
    Returns:
        dict: Batch parsing results
    """
    results = {
        'success': 0,
        'failed': 0,
        'total': len(resume_ids),
    }
    
    for resume_id in resume_ids:
        result = parse_resume_async.delay(resume_id)
        
        # Note: This won't wait for completion, just queues the tasks
        # For synchronous batch processing, use parse_resume_async.apply() instead
    
    logger.info(f"Queued {len(resume_ids)} resumes for parsing")
    
    return results


@shared_task
def cleanup_old_failed_resumes(days=30):
    """
    Delete old failed resume files to save storage.
    
    Args:
        days: Delete files older than this many days
        
    Returns:
        int: Number of files cleaned up
    """
    from .models import Resume
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    old_failed_resumes = Resume.objects.filter(
        status='failed',
        uploaded_at__lt=cutoff_date
    )
    
    count = old_failed_resumes.count()
    
    for resume in old_failed_resumes:
        try:
            resume.delete()  # Will also delete file from storage
        except Exception as e:
            logger.error(f"Error deleting resume {resume.pk}: {str(e)}")
    
    logger.info(f"Cleaned up {count} old failed resumes")
    
    return count


@shared_task
def reparse_failed_resumes():
    """
    Retry parsing for all failed resumes.
    
    Returns:
        dict: Reparse results
    """
    from .models import Resume
    
    failed_resumes = Resume.objects.filter(status='failed')
    
    results = {
        'queued': 0,
        'total': failed_resumes.count(),
    }
    
    for resume in failed_resumes:
        if resume.can_reparse:
            parse_resume_async.delay(resume.pk)
            results['queued'] += 1
    
    logger.info(f"Queued {results['queued']} failed resumes for re-parsing")
    
    return results


# Periodic tasks (configure in settings.py with celery beat)
@shared_task
def daily_resume_maintenance():
    """
    Daily maintenance task for resumes.
    Run this with celery beat scheduler.
    """
    from .models import Resume
    
    # Get stuck parsing resumes (parsing for more than 1 hour)
    from datetime import timedelta
    stuck_cutoff = timezone.now() - timedelta(hours=1)
    
    stuck_resumes = Resume.objects.filter(
        status='parsing',
        last_parse_attempt__lt=stuck_cutoff
    )
    
    # Reset stuck resumes to uploaded
    stuck_count = stuck_resumes.update(
        status='uploaded',
        error_message='Parsing timed out'
    )
    
    logger.info(f"Reset {stuck_count} stuck resumes")
    
    return {
        'stuck_resumes_reset': stuck_count,
    }


@shared_task(bind=True, max_retries=3)
def process_ai_rewrite_with_template(self, session_id):
    """
    Process AI rewrite with template awareness
    
    Args:
        session_id: ID of the AIRewriteSession object
        
    Returns:
        dict: Processing result
    """
    from .models import AIRewriteSession
    from .ai_template_rewriter import TemplateAwareRewriter
    
    try:
        # Get session
        session = AIRewriteSession.objects.get(id=session_id)
        session.mark_as_processing()
        
        logger.info(
            f"Starting AI rewrite for session {session_id} "
            f"using {session.llm_provider}"
        )
        
        # Initialize rewriter
        rewriter = TemplateAwareRewriter(llm_provider=session.llm_provider)
        
        # Prepare context
        context = {
            'job_title': session.job_title,
            'industry': session.industry,
            'highlights': session.highlights,
            'metrics_focus': session.metrics_focus,
            'job_description': session.job_description,
            'additional_instructions': session.additional_instructions,
        }
        
        # Rewrite
        rewritten_text, tokens, processing_time = rewriter.rewrite_with_template(
            resume_text=session.original_content,
            template=session.template,
            context=context
        )
        
        # Update session
        session.mark_as_completed(rewritten_text, tokens, processing_time)
        
        # Increment template usage
        if session.template:
            session.template.increment_usage()
        
        logger.info(
            f"AI rewrite completed for session {session_id}: "
            f"{tokens} tokens, {processing_time:.2f}s"
        )
        
        return {
            'success': True,
            'session_id': session_id,
            'tokens_used': tokens,
            'processing_time': processing_time,
        }
        
    except AIRewriteSession.DoesNotExist:
        logger.error(f"AIRewriteSession {session_id} not found")
        raise
        
    except Exception as e:
        logger.error(f"AI rewrite failed for session {session_id}: {e}")
        
        # Mark session as failed
        try:
            session = AIRewriteSession.objects.get(id=session_id)
            session.mark_as_failed(str(e))
        except:
            pass
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))