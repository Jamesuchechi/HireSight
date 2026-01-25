"""
AI module for interview practice sessions.

Delegates all generation tasks to AIConnector for centralized AI service handling.
"""
import json
import logging

import requests
from django.conf import settings
from .ai_connector import AIConnector
from django.core.cache import cache
import hashlib
import json as _json

logger = logging.getLogger(__name__)

# Initialize AIConnector
_ai_connector = AIConnector()

MISTRAL_BASE_URL = (
    getattr(settings, 'INTERVIEW_PRACTICE_MISTRAL_BASE_URL', None)
    or getattr(settings, 'MISTRAL_AI_BASE_URL', 'https://api.mistral.ai/v1')
)
MISTRAL_MODEL = (
    getattr(settings, 'INTERVIEW_PRACTICE_MISTRAL_MODEL', None)
    or getattr(settings, 'MISTRAL_AI_MODEL', 'mistral-small-latest')
)
MISTRAL_API_URL = getattr(
    settings,
    'INTERVIEW_PRACTICE_MISTRAL_URL',
    f"{MISTRAL_BASE_URL}/models/{MISTRAL_MODEL}/completions"
)
MISTRAL_API_KEY = (
    getattr(settings, 'INTERVIEW_PRACTICE_MISTRAL_API_KEY', None)
    or getattr(settings, 'MISTRAL_AI_API_KEY', '')
)
MISTRAL_TIMEOUT = getattr(settings, 'INTERVIEW_PRACTICE_MISTRAL_TIMEOUT', None) or getattr(settings, 'MISTRAL_AI_TIMEOUT', 30)


def _safe_call(payload):
    """Make a Mistral API call with proper error handling."""
    if not MISTRAL_API_KEY:
        raise RuntimeError("Mistral API key not configured")

    headers = {
        'Authorization': f'Bearer {MISTRAL_API_KEY}',
        'Content-Type': 'application/json',
    }

    resp = requests.post(MISTRAL_API_URL, json=payload, headers=headers, timeout=MISTRAL_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _extract_text(response_data):
    """Extract text content from various API response formats."""
    if not isinstance(response_data, dict):
        return ''

    for key in ('output', 'outputs', 'results', 'choices'):
        candidate = response_data.get(key)
        if candidate:
            if isinstance(candidate, list):
                first = candidate[0]
                if isinstance(first, dict):
                    content = first.get('content') or first.get('message') or first
                    if isinstance(content, list):
                        return ''.join(item.get('text', '') for item in content if isinstance(item, dict))
                    if isinstance(content, str):
                        return content
                if isinstance(first, str):
                    return first
            if isinstance(candidate, dict):
                return candidate.get('text', '')

    return response_data.get('text', '')


def _parse_questions(text):
    """Parse questions from API response text."""
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed.get('questions') or parsed.get('items') or []
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return [{'prompt': line, 'category': 'General', 'difficulty': 'Intermediate'} for line in lines[:3]] or [
        {'prompt': text, 'category': 'General', 'difficulty': 'Intermediate'}
    ]


def generate_questions(session):
    """
    Generate practice interview questions using AIConnector.
    
    Attempts Gemini first with full fallback, then Mistral as final fallback.
    Never returns fake/hardcoded questions.
    
    Args:
        session: InterviewPracticeSession instance
        
    Returns:
        tuple: (questions_list, raw_response, model_used) where:
               - questions_list: list of validated questions or empty list if generation fails
               - raw_response: str with the raw AI response or error message
               - model_used: str with 'gemini', 'mistral', or None if failed
    """
    # Cache questions for identical session settings for 1 hour
    try:
        key_source = _json.dumps({
            'candidate': getattr(session.candidate, 'id', None),
            'application': getattr(session.application, 'id', None),
            'settings': session.settings or {}
        }, sort_keys=True, default=str)
        cache_key = 'ai:questions:' + hashlib.sha256(key_source.encode('utf-8')).hexdigest()
        cached = cache.get(cache_key)
        if cached:
            # Only return cached result if it contains questions (avoid caching failures)
            if cached.get('questions'):
                return cached.get('questions', []), cached.get('raw_response'), cached.get('model_used')
            else:
                try:
                    cache.delete(cache_key)
                except Exception:
                    pass

        questions, raw_response, model_used = _ai_connector.generate_questions(session)
        logger.info(
            f"AI-generated {len(questions)} questions using {model_used or 'fallback'} "
            f"for session {session.id}"
        )
        # Store in cache for 1 hour
        try:
            cache.set(cache_key, {'questions': questions, 'raw_response': raw_response, 'model_used': model_used}, timeout=60 * 60)
        except Exception:
            pass
        return questions, raw_response, model_used
    except Exception as exc:
        logger.error(f"Failed to generate questions through AIConnector: {exc}")
        return [], str(exc), None


def score_response(question_prompt, text_response, video_url):
    payload = {
        'input': f"Score the candidate response to this prompt: {question_prompt}\n"
                 f"Text answer: {text_response}\nVideo URL: {video_url or 'N/A'}",
        'temperature': 0.3
    }

    # Cache scoring results for identical prompt+answer for 1 hour
    try:
        key = hashlib.sha256((question_prompt + '||' + (text_response or '')).encode('utf-8')).hexdigest()
        cache_key = f'ai:score:{key}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        data = _safe_call(payload)
        text = _extract_text(data)
        parsed = json.loads(text)
        result = {
            'score': parsed.get('score', 0),
            'feedback': parsed.get('feedback', 'Clear structure; add more detail.'),
            'analysis': parsed.get('analysis', {'focus': 'steady', 'confidence': 0.7}),
            'request_id': parsed.get('request_id', 'ai-score')
        }
        try:
            cache.set(cache_key, result, timeout=60 * 60)
        except Exception:
            pass
        return result
    except Exception as exc:
        logger.debug("Fallback scoring: %s", exc)
        return {
            'score': 80,
            'feedback': 'Maintain composure and add more quantifiable results.',
            'analysis': {'focus': 'steady', 'confidence': 0.72},
            'request_id': 'fake-score'
        }


def summarize_session(session):
    payload = {
        'input': f"Summarize the practice session for {session.candidate.email}. "
                 f"Focus on strengths, weaknesses, and recommendations."
    }
    # Cache reports per session for 1 hour
    try:
        cache_key = f"ai:report:session:{getattr(session, 'id', '')}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        data = _safe_call(payload)
        text = _extract_text(data)
        parsed = json.loads(text)
        result = {
            'overall_score': parsed.get('overall_score', 0),
            'strengths': parsed.get('strengths', []),
            'weaknesses': parsed.get('weaknesses', []),
            'recommendations': parsed.get('recommendations', ''),
            'request_id': parsed.get('request_id', 'ai-report')
        }
        try:
            cache.set(cache_key, result, timeout=60 * 60)
        except Exception:
            pass
        return result
    except Exception as exc:
        logger.debug("Fallback report generation: %s", exc)
        return {
            'overall_score': 0,
            'strengths': ['Clear explanations', 'Poised delivery'],
            'weaknesses': ['Need more data-driven proof', 'Expand depth on technical choices'],
            'recommendations': 'Try rephrasing answers using STAR; revisit the recorded sessions.',
            'request_id': 'fake-report'
        }
