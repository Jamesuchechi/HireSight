"""
Celery tasks for progress tracking and real-time updates.
Handles question generation progress, report generation progress, and WebSocket notifications.
"""
import json
import logging
from celery import shared_task, group
from django.core.cache import cache
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task
from .models import InterviewPracticeSession
from apps.interviews import ai_connector, utils

logger = logging.getLogger(__name__)


@shared_task
def track_question_generation_progress(session_id, progress_data):
    """
    Track and broadcast question generation progress to connected WebSocket clients.
    
    Args:
        session_id: UUID of the practice session
        progress_data: Dict with progress information
    """
    try:
        # Store progress in cache for polling clients
        cache_key = f'session_progress:{session_id}'
        cache.set(cache_key, progress_data, timeout=3600)
        
        # Broadcast to WebSocket clients
        channel_layer = get_channel_layer()
        
        # Send progress update to session-specific group
        async_to_sync(channel_layer.group_send)(
            f'session_{session_id}',
            {
                'type': 'progress_update',
                'data': progress_data
            }
        )
        
        logger.info(f"Progress update sent for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error tracking progress for session {session_id}: {e}")


@shared_task
def track_report_generation_progress(session_id, stage, status):
    """
    Track report generation progress through different stages.
    
    Args:
        session_id: UUID of the practice session
        stage: Current stage (analyzing, scoring, generating_insights, etc.)
        status: Current status (in_progress, completed, failed)
    """
    from .models import InterviewPracticeSession
    
    try:
        session = InterviewPracticeSession.objects.get(id=session_id)
        
        # Update session state
        if status == 'in_progress':
            session.report_generation_state = InterviewPracticeSession.GenerationState.IN_PROGRESS
        elif status == 'completed':
            session.report_generation_state = InterviewPracticeSession.GenerationState.COMPLETED
        elif status == 'failed':
            session.report_generation_state = InterviewPracticeSession.GenerationState.FAILED
        
        session.save()
        
        # Broadcast progress
        progress_data = {
            'type': 'report_generation',
            'session_id': str(session_id),
            'stage': stage,
            'status': status,
            'timestamp': timezone.now().isoformat()
        }
        
        track_question_generation_progress.delay(session_id, progress_data)
        
        logger.info(f"Report generation progress: {stage} - {status}")
        
    except Exception as e:
        logger.error(f"Error tracking report generation for session {session_id}: {e}")


@shared_task
def broadcast_session_update(session_id, update_type, data):
    """
    Broadcast any session update to connected clients via WebSocket.
    
    Args:
        session_id: UUID of the practice session
        update_type: Type of update (session_started, question_analyzed, session_completed, etc.)
        data: Update data payload
    """
    try:
        channel_layer = get_channel_layer()
        
        message = {
            'type': 'session_update',
            'update_type': update_type,
            'data': data,
            'timestamp': timezone.now().isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(
            f'session_{session_id}',
            message
        )
        
        logger.info(f"Session update broadcast: {update_type}")
        
    except Exception as e:
        logger.error(f"Error broadcasting session update: {e}")


def get_session_progress(session_id):
    """
    Get cached progress information for a session.
    
    Args:
        session_id: UUID of the practice session
        
    Returns:
        dict with current progress or None if not found
    """
    cache_key = f'session_progress:{session_id}'
    progress = cache.get(cache_key)
    
    if progress:
        return progress
    
    # Return default if not in cache
    return {
        'type': 'session_progress',
        'session_id': str(session_id),
        'progress': 0,
        'status': 'pending',
        'message': 'Initializing session...'
    }


@shared_task
def simulate_question_generation_progress(session_id, total_questions):
    """
    Simulate and broadcast question generation progress (for demo/testing).
    
    Args:
        session_id: UUID of the practice session
        total_questions: Total number of questions to generate
    """
    from .models import InterviewPracticeSession
    
    stages = [
        {'stage': 'analyzing', 'message': 'Analyzing job requirements...'},
        {'stage': 'matching', 'message': 'Matching questions to skills...'},
        {'stage': 'generating', 'message': f'Generating {total_questions} personalized questions...'},
        {'stage': 'validating', 'message': 'Validating questions...'},
        {'stage': 'completed', 'message': 'Ready!'},
    ]
    
    try:
        session = InterviewPracticeSession.objects.get(id=session_id)
        session.question_generation_state = InterviewPracticeSession.GenerationState.IN_PROGRESS
        session.save()
        
        for stage_idx, stage_info in enumerate(stages):
            # Calculate progress
            progress = int((stage_idx / len(stages)) * 100)
            
            progress_data = {
                'type': 'generation_progress',
                'session_id': str(session_id),
                'stage': stage_info['stage'],
                'message': stage_info['message'],
                'progress': progress,
                'total_stages': len(stages),
                'current_stage': stage_idx + 1,
                'timestamp': timezone.now().isoformat()
            }
            
            # Broadcast progress
            track_question_generation_progress.delay(session_id, progress_data)
            
            # Small delay between stages
            if stage_idx < len(stages) - 1:
                from time import sleep
                sleep(1)
        
        # Mark as completed
        session.question_generation_state = InterviewPracticeSession.GenerationState.COMPLETED
        session.save()
        
        # Final notification
        completed_data = {
            'type': 'generation_complete',
            'session_id': str(session_id),
            'questions_generated': total_questions,
            'timestamp': timezone.now().isoformat()
        }
        
        broadcast_session_update.delay(session_id, 'questions_ready', completed_data)
        
    except Exception as e:
        logger.error(f"Error simulating progress for session {session_id}: {e}")
        session.question_generation_state = InterviewPracticeSession.GenerationState.FAILED
        session.save()


@shared_task
def track_warmup_completion(session_id, warmup_data):
    """
    Record warmup completion with test results.
    
    Args:
        session_id: UUID of the practice session
        warmup_data: Dict with camera, microphone, and test question results
    """
    from .models import InterviewPracticeSession
    
    try:
        session = InterviewPracticeSession.objects.get(id=session_id)
        
        # Update warmup status
        session.warmup_completed = True
        session.camera_test_passed = warmup_data.get('camera_test_passed', False)
        session.microphone_test_passed = warmup_data.get('microphone_test_passed', False)
        session.test_question_completed = warmup_data.get('test_question_completed', False)
        
        # Store warmup metadata
        session.settings['warmup_data'] = {
            'camera_quality': warmup_data.get('camera_quality'),
            'audio_level': warmup_data.get('audio_level'),
            'test_question_score': warmup_data.get('test_question_score'),
            'completed_at': timezone.now().isoformat()
        }
        
        session.save()
        
        # Notify clients
        warmup_complete_data = {
            'type': 'warmup_complete',
            'session_id': str(session_id),
            'camera_passed': session.camera_test_passed,
            'microphone_passed': session.microphone_test_passed,
            'ready_to_start': all([
                session.camera_test_passed,
                session.microphone_test_passed
            ]),
            'timestamp': timezone.now().isoformat()
        }
        
        broadcast_session_update.delay(session_id, 'warmup_complete', warmup_complete_data)
        
        logger.info(f"Warmup completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error tracking warmup completion for session {session_id}: {e}")


@shared_task
def track_response_analysis(session_id, response_id, analysis_result):
    """
    Broadcast response analysis completion.
    
    Args:
        session_id: UUID of the practice session
        response_id: ID of the practice response
        analysis_result: Dict with analysis/scoring results
    """
    from .models import InterviewPracticeSession
    
    try:
        session = InterviewPracticeSession.objects.get(id=session_id)
        
        # Count completed responses
        from .models import PracticeResponse
        responses = PracticeResponse.objects.filter(session=session)
        completed = responses.filter(overall_score__isnull=False).count()
        total = session.number_of_questions or responses.count()
        progress_percent = int((completed / total * 100) if total > 0 else 0)
        
        # Calculate average score so far
        scores = [float(r.overall_score or 0) for r in responses if r.overall_score]
        avg_score = sum(scores) / len(scores) if scores else None
        
        analysis_data = {
            'type': 'response_analyzed',
            'session_id': str(session_id),
            'response_id': response_id,
            'score': analysis_result.get('overall_score'),
            'feedback': analysis_result.get('feedback'),
            'progress': {
                'completed': completed,
                'total': total,
                'percentage': progress_percent
            },
            'average_score': avg_score,
            'timestamp': timezone.now().isoformat()
        }
        
        broadcast_session_update.delay(session_id, 'response_analyzed', analysis_data)
        
        logger.info(f"Response {response_id} analysis tracked for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error tracking response analysis for session {session_id}: {e}")


@shared_task
def track_session_pause(session_id, pause_reason=None):
    """
    Track when a session is paused.
    
    Args:
        session_id: UUID of the practice session
        pause_reason: Optional reason for pause
    """
    pause_data = {
        'type': 'session_paused',
        'session_id': str(session_id),
        'reason': pause_reason,
        'paused_at': timezone.now().isoformat()
    }
    
    broadcast_session_update.delay(session_id, 'session_paused', pause_data)


@shared_task
def track_session_resume(session_id):
    """
    Track when a session is resumed.
    
    Args:
        session_id: UUID of the practice session
    """
    resume_data = {
        'type': 'session_resumed',
        'session_id': str(session_id),
        'resumed_at': timezone.now().isoformat()
    }
    
    broadcast_session_update.delay(session_id, 'session_resumed', resume_data)


@shared_task
def track_question_skip(session_id, question_id):
    """
    Track when a question is skipped.
    
    Args:
        session_id: UUID of the practice session
        question_id: ID of the skipped question
    """
    skip_data = {
        'type': 'question_skipped',
        'session_id': str(session_id),
        'question_id': question_id,
        'skipped_at': timezone.now().isoformat()
    }
    
    broadcast_session_update.delay(session_id, 'question_skipped', skip_data)


@shared_task
def track_question_rerecord(session_id, question_id):
    """
    Track when a question response is re-recorded.
    
    Args:
        session_id: UUID of the practice session
        question_id: ID of the re-recorded question
    """
    rerecord_data = {
        'type': 'question_rerecorded',
        'session_id': str(session_id),
        'question_id': question_id,
        'rerecorded_at': timezone.now().isoformat()
    }
    
    broadcast_session_update.delay(session_id, 'question_rerecorded', rerecord_data)



@shared_task
def generate_warmup_question_task(session_id):
    logger.info(f"Starting warmup question generation task for session {session_id}")
    try:
        session = InterviewPracticeSession.objects.get(pk=session_id)
        session.warmup_question_state = InterviewPracticeSession.GenerationState.IN_PROGRESS
        session.save(update_fields=['warmup_question_state'])

        prompt = "Generate one simple, non-technical interview warmup question. The question should be something a candidate can answer to get comfortable, like 'Tell me about yourself' or 'What is a project you are proud of?'. Return only the question text, no JSON, no extra formatting."

        warmup_question = utils.generate_text_with_fallback(prompt, json_mode=False)

        if warmup_question.startswith("Error:"):
            logger.error(f"Failed to generate warmup question for session {session_id}: {warmup_question}")
            raise Exception(warmup_question)

        # The response might be in JSON if the model defaults to it, let's try to parse.
        try:
            data = json.loads(warmup_question)
            if 'question' in data:
                warmup_question = data['question']
            elif 'message' in data:
                warmup_question = data['message']
        except (json.JSONDecodeError, TypeError):
            # It's likely plain text, which is what we want.
            pass

        session.warmup_question_prompt = warmup_question.strip().strip('"')
        session.warmup_question_state = InterviewPracticeSession.GenerationState.COMPLETED
        session.save(update_fields=['warmup_question_prompt', 'warmup_question_state'])
        logger.info(f"Generated warmup question for session {session_id}")
    except InterviewPracticeSession.DoesNotExist:
        logger.error(f"Session {session_id} not found for warmup question generation.")
        pass
    except Exception as e:
        logger.error(f"Error generating warmup question for session {session_id}: {e}")
        if 'session' in locals() and isinstance(session, InterviewPracticeSession):
            session.warmup_question_state = InterviewPracticeSession.GenerationState.FAILED
            session.save(update_fields=['warmup_question_state'])