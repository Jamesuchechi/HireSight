"""
Mistral AI integration service for screening insights.
"""
import json
import time
import logging
from typing import Optional, Dict, List, Any
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class MistralAIService:
    """Service for interacting with Mistral AI API."""

    def __init__(self):
        """Initialize Mistral AI service."""
        self.api_key = getattr(settings, 'MISTRAL_API_KEY', None)
        self.api_url = "https://api.mistral.ai/v1/messages"
        self.model = getattr(settings, 'MISTRAL_MODEL', 'mistral-7b-instruct')
        self.max_tokens = getattr(settings, 'MISTRAL_MAX_TOKENS', 2048)

        if not self.api_key:
            logger.warning("Mistral API key not configured")

    def _make_request(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Make a request to Mistral API."""
        if not self.api_key:
            raise ValueError("Mistral API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.7,
        }

        try:
            start_time = time.time()
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            generation_time = time.time() - start_time

            response.raise_for_status()
            data = response.json()

            return {
                'success': True,
                'content': data['choices'][0]['message']['content'],
                'tokens_used': data.get('usage', {}).get('completion_tokens', 0),
                'generation_time': generation_time,
            }

        except requests.exceptions.Timeout:
            logger.error("Mistral API request timeout")
            return {
                'success': False,
                'error': 'API request timeout',
                'generation_time': time.time() - start_time,
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Mistral API request error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'generation_time': time.time() - start_time,
            }

        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Mistral API response parsing error: {str(e)}")
            return {
                'success': False,
                'error': 'Invalid API response',
                'generation_time': time.time() - start_time,
            }

    def generate_interview_questions(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Generate interview questions based on resume and job description."""
        system_prompt = """You are an expert recruiter and interviewer. Generate insightful interview questions 
        for a candidate based on their resume and the job description. Focus on relevant experience and gaps.
        Return response as JSON with this format: {"questions": [{"question": "...", "category": "...", "difficulty": "..."}, ...]}"""

        prompt = f"""Resume:
{resume_text}

Job Description:
{job_description}

Generate 5-8 tailored interview questions."""

        result = self._make_request(prompt, system_prompt)

        if result['success']:
            try:
                # Parse JSON response
                content = result['content']
                # Extract JSON from response (might have extra text)
                if '{' in content and '}' in content:
                    json_start = content.index('{')
                    json_end = content.rindex('}') + 1
                    json_str = content[json_start:json_end]
                    questions_data = json.loads(json_str)
                else:
                    questions_data = json.loads(content)

                return {
                    'success': True,
                    'questions': questions_data.get('questions', []),
                    'tokens_used': result['tokens_used'],
                    'generation_time': result['generation_time'],
                }
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse interview questions: {str(e)}")
                return {
                    'success': False,
                    'error': f'Failed to parse response: {str(e)}',
                    'generation_time': result['generation_time'],
                }

        return {
            'success': False,
            'error': result.get('error', 'Unknown error'),
            'generation_time': result.get('generation_time', 0),
        }

    def generate_ai_notes(self, resume_text: str, match_score: float, key_findings: str) -> Dict[str, Any]:
        """Generate AI notes for a screening result."""
        system_prompt = """You are an expert HR analyst. Analyze the candidate information and provide concise, 
        actionable notes for recruiters. Return response as JSON with format: 
        {"notes": [{"title": "...", "content": "..."}, ...], "summary": "..."}"""

        prompt = f"""Candidate Resume:
{resume_text}

Match Score: {match_score}%

Key Findings:
{key_findings}

Generate professional notes highlighting strengths, potential concerns, and recommendations."""

        result = self._make_request(prompt, system_prompt)

        if result['success']:
            try:
                content = result['content']
                if '{' in content and '}' in content:
                    json_start = content.index('{')
                    json_end = content.rindex('}') + 1
                    json_str = content[json_start:json_end]
                    notes_data = json.loads(json_str)
                else:
                    notes_data = json.loads(content)

                return {
                    'success': True,
                    'notes': notes_data.get('notes', []),
                    'summary': notes_data.get('summary', ''),
                    'tokens_used': result['tokens_used'],
                    'generation_time': result['generation_time'],
                }
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse AI notes: {str(e)}")
                return {
                    'success': False,
                    'error': f'Failed to parse response: {str(e)}',
                    'generation_time': result['generation_time'],
                }

        return {
            'success': False,
            'error': result.get('error', 'Unknown error'),
            'generation_time': result.get('generation_time', 0),
        }

    def generate_rejection_reasons(self, resume_text: str, job_description: str, match_score: float) -> Dict[str, Any]:
        """Generate reasons for candidate rejection (when score is low)."""
        system_prompt = """You are an experienced recruiter. Based on the candidate and job information, 
        provide constructive, professional reasons if they don't match. Return JSON format:
        {"reasons": [{"title": "...", "description": "...", "severity": "..."}, ...], "recommendation": "..."}"""

        prompt = f"""Candidate Resume:
{resume_text}

Job Description:
{job_description}

Match Score: {match_score}%

Provide constructive feedback on why this candidate may not be a good fit, with severity levels and recommendations."""

        result = self._make_request(prompt, system_prompt)

        if result['success']:
            try:
                content = result['content']
                if '{' in content and '}' in content:
                    json_start = content.index('{')
                    json_end = content.rindex('}') + 1
                    json_str = content[json_start:json_end]
                    reasons_data = json.loads(json_str)
                else:
                    reasons_data = json.loads(content)

                return {
                    'success': True,
                    'reasons': reasons_data.get('reasons', []),
                    'recommendation': reasons_data.get('recommendation', ''),
                    'tokens_used': result['tokens_used'],
                    'generation_time': result['generation_time'],
                }
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse rejection reasons: {str(e)}")
                return {
                    'success': False,
                    'error': f'Failed to parse response: {str(e)}',
                    'generation_time': result['generation_time'],
                }

        return {
            'success': False,
            'error': result.get('error', 'Unknown error'),
            'generation_time': result.get('generation_time', 0),
        }

    def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """Extract structured information from resume."""
        system_prompt = """You are an expert resume parser. Extract and structure key information from the resume.
        Return JSON format: {"name": "...", "email": "...", "phone": "...", "skills": [...], 
        "experience": [...], "education": [...], "certifications": [...], "summary": "..."}"""

        prompt = f"""Resume:
{resume_text}

Extract and structure all key information in JSON format."""

        result = self._make_request(prompt, system_prompt)

        if result['success']:
            try:
                content = result['content']
                if '{' in content and '}' in content:
                    json_start = content.index('{')
                    json_end = content.rindex('}') + 1
                    json_str = content[json_start:json_end]
                    parsed_data = json.loads(json_str)
                else:
                    parsed_data = json.loads(content)

                return {
                    'success': True,
                    'parsed_data': parsed_data,
                    'tokens_used': result['tokens_used'],
                    'generation_time': result['generation_time'],
                }
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse resume: {str(e)}")
                return {
                    'success': False,
                    'error': f'Failed to parse response: {str(e)}',
                    'generation_time': result['generation_time'],
                }

        return {
            'success': False,
            'error': result.get('error', 'Unknown error'),
            'generation_time': result.get('generation_time', 0),
        }

    def batch_generate_insights(self, insights_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate multiple insights in batch."""
        results = []

        for insight_config in insights_list:
            insight_type = insight_config.get('type')
            data = insight_config.get('data', {})

            if insight_type == 'interview_questions':
                result = self.generate_interview_questions(
                    data.get('resume_text', ''),
                    data.get('job_description', '')
                )
            elif insight_type == 'ai_notes':
                result = self.generate_ai_notes(
                    data.get('resume_text', ''),
                    data.get('match_score', 0),
                    data.get('key_findings', '')
                )
            elif insight_type == 'rejection_reasons':
                result = self.generate_rejection_reasons(
                    data.get('resume_text', ''),
                    data.get('job_description', ''),
                    data.get('match_score', 0)
                )
            elif insight_type == 'resume_parsing':
                result = self.parse_resume(data.get('resume_text', ''))
            else:
                result = {'success': False, 'error': f'Unknown insight type: {insight_type}'}

            results.append({
                'type': insight_type,
                'result': result,
            })

        return results
