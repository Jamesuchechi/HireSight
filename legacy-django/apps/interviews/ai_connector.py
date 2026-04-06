"""
AI Connector for Interview Practice Sessions - Using Mistral SDK

Handles integration with Mistral AI using the mistralai package (same as assessments).
Falls back to Groq when Mistral is unavailable.
"""
import json
import logging
import time
from django.conf import settings

logger = logging.getLogger(__name__)

# Import Mistral SDK (same as assessments)
try:
    from mistralai import Mistral
except ImportError:
    Mistral = None
    logger.warning("mistralai package not installed. Run: pip install mistralai")

# Import Groq SDK (fallback AI)
try:
    from groq import Groq
except ImportError:
    Groq = None
    logger.warning("groq package not installed. Run: pip install groq")


class PromptBuilder:
    """Production-ready prompt builder for interview practice AI calls."""

    DEFAULT_MAX_DESC = 1000

    def __init__(self, context=None, *, language='en', max_job_desc_len=None):
        self.context = context or {}
        self.language = language or 'en'
        self.max_job_desc_len = max_job_desc_len or self.DEFAULT_MAX_DESC

    def _sanitize(self, text):
        if text is None:
            return ''
        s = str(text)
        s = ''.join(ch for ch in s if ord(ch) >= 32 or ch in '\n\t')
        return s.strip()

    def _list_to_csv(self, items):
        if not items:
            return ''
        return ', '.join([self._sanitize(i) for i in items if i])

    def build_prompt(self):
        ctx = self.context or {}
        role_title = self._sanitize(ctx.get('role_title') or ctx.get('role') or 'Candidate')
        job_desc_raw = ctx.get('job_description') or ''
        job_desc = self._sanitize(job_desc_raw)[:self.max_job_desc_len]
        required_skills = ctx.get('required_skills') or ctx.get('skills') or []
        focus_areas = ctx.get('focus_areas') or []
        difficulty = self._sanitize(ctx.get('difficulty') or 'medium')
        number_of_questions = int(ctx.get('number_of_questions') or 5)

        parts = []
        parts.append(f"Role/Position: {role_title}")
        if job_desc:
            parts.append(f"Job Description Summary: {job_desc}")

        skills_csv = self._list_to_csv(required_skills)
        if skills_csv:
            parts.append(f"Key Skills: {skills_csv}")

        focus_csv = self._list_to_csv(focus_areas)
        if focus_csv:
            parts.append(f"Focus Areas: {focus_csv}")

        parts.append(f"Difficulty Level: {difficulty}")
        parts.append(f"Number of Questions: {number_of_questions}")
        parts.append(f"Language: {self.language}")

        schema = (
            "Respond with ONLY a JSON object (no markdown or explanations). Follow this schema exactly:\n"
            "{\n  \"questions\": [\n    {\n      \"prompt\": \"string\",\n      \"category\": \"behavioral|technical|situational\",\n      \"difficulty\": \"easy|medium|hard\",\n      \"evaluation_criteria\": [\"criterion1\", \"criterion2\"],\n      \"order\": 1,\n      \"expected_answer_elements\": [\"element1\", \"element2\"]\n    }\n  ]\n}\n"
        )

        parts.append(schema)
        parts.append("Ensure variety across categories and difficulty, and tailor to the role and skills when provided.")
        parts.append("Return exactly the requested number of questions.")

        prompt = "\n\n".join(parts)
        return prompt


class VideoMetricsParser:
    """Parse and normalize video analysis metrics."""

    def parse(self, metrics):
        if metrics is None:
            return {}

        if not isinstance(metrics, dict):
            raise ValueError('metrics must be a dict')

        out = {}
        for section in ('eye_contact', 'head_stability', 'speaking', 'engagement', 'audio'):
            raw = metrics.get(section)
            if raw is None:
                out[section] = None
            else:
                out[section] = dict(raw or {})

        ec = out['eye_contact'] or {}
        for key in ('frames_with_contact', 'total_frames', 'percentage'):
            if key in ec:
                try:
                    if ec[key] is None:
                        ec[key] = 0
                    else:
                        if isinstance(ec[key], str):
                            ec[key] = ec[key].strip()
                        ec[key] = float(ec[key]) if ec[key] != '' else 0
                        if key != 'percentage' and float(ec[key]).is_integer():
                            ec[key] = int(ec[key])
                except Exception:
                    ec[key] = 0 if key != 'percentage' else 0.0

        frames_with = ec.get('frames_with_contact') if ec is not None else None
        total_frames = ec.get('total_frames') if ec is not None else None
        if ec is not None and ('percentage' not in ec or ec.get('percentage') in (None, 0)):
            try:
                if total_frames:
                    ec['percentage'] = round((float(frames_with or 0) / float(total_frames)) * 100, 1)
                else:
                    ec['percentage'] = 0.0
            except Exception:
                ec['percentage'] = 0.0

        hs = out['head_stability']
        if hs is not None:
            for key in ('movement_pixels', 'max_movement_pixels', 'max_movement', 'stability_score'):
                if key in hs:
                    try:
                        if hs[key] is None:
                            hs[key] = 0
                        else:
                            hs[key] = float(hs[key])
                    except Exception:
                        hs[key] = 0.0

            if 'stability_score' not in hs or hs.get('stability_score') in (None, 0):
                movement = hs.get('movement_pixels') or hs.get('movement') or 0
                max_m = hs.get('max_movement_pixels') or hs.get('max_movement') or 100
                hs['stability_score'] = self.calculate_head_stability_score(movement, max_m)

        return out

    def calculate_eye_contact_percentage(self, frames_with_contact, total_frames):
        try:
            if not total_frames:
                return 0.0
            return round((frames_with_contact / total_frames) * 100, 1)
        except Exception:
            return 0.0

    def calculate_head_stability_score(self, movement_pixels, max_movement):
        try:
            movement = float(movement_pixels or 0)
            max_m = float(max_movement or 100)
            if max_m <= 0:
                return 0.0
            ratio = movement / max_m
            score = 1.0 - ratio
            score = max(0.0, min(1.0, score))
            return round(score, 3)
        except Exception:
            return 0.0

    def aggregate_metrics(self, metrics):
        """Aggregate parsed metrics into an overall presence score (0-100)."""
        try:
            parsed = self.parse(metrics)
        except Exception:
            return 0.0

        ec = parsed.get('eye_contact', {})
        hs = parsed.get('head_stability', {})
        sp = parsed.get('speaking', {})

        eye_pct = float(ec.get('percentage') or 0.0)
        head_score = float(hs.get('stability_score') or 0.0)
        head_pct = head_score * 100.0
        speak_consistency = float(sp.get('speech_rate_consistency') or 0.0) * 100.0

        overall = (0.4 * eye_pct) + (0.35 * head_pct) + (0.25 * speak_consistency)
        return round(overall, 1)


class ValidationError(Exception):
    """Custom exception for question validation errors."""
    pass


class QuestionValidator:
    """Validates AI-generated questions against the expected schema."""
    
    VALID_CATEGORIES = {'behavioral', 'technical', 'situational'}
    VALID_DIFFICULTIES = {'easy', 'medium', 'hard', 'beginner', 'intermediate', 'advanced'}
    
    @staticmethod
    def normalize_difficulty(difficulty):
        """Map various difficulty formats to standard values."""
        if not difficulty:
            return 'medium'
        
        difficulty_lower = str(difficulty).lower().strip()
        
        mapping = {
            'beginner': 'easy',
            'intermediate': 'medium',
            'advanced': 'hard',
            'easy': 'easy',
            'medium': 'medium',
            'hard': 'hard',
            'junior': 'easy',
            'senior': 'hard',
            'entry': 'easy',
            'expert': 'hard',
        }
        
        return mapping.get(difficulty_lower, 'medium')
    
    @staticmethod
    def normalize_category(category):
        """Map various category formats to standard values."""
        if not category:
            return 'behavioral'
        
        category_lower = str(category).lower().strip()
        
        mapping = {
            'behavioral': 'behavioral',
            'behaviour': 'behavioral',
            'behavioral_': 'behavioral',
            'technical': 'technical',
            'technical_': 'technical',
            'system design': 'technical',
            'situational': 'situational',
            'scenario': 'situational',
            'hypothetical': 'situational',
            'general': 'behavioral',
            'cultural': 'situational',
        }
        
        return mapping.get(category_lower, 'behavioral')
    
    @classmethod
    def validate(cls, raw_response):
        """Validate JSON response against schema."""
        if not isinstance(raw_response, dict):
            raise ValidationError("Response must be a dictionary")
        
        questions = raw_response.get('questions', [])
        if not isinstance(questions, list):
            raise ValidationError("'questions' field must be a list")
        
        if not questions:
            raise ValidationError("No questions found in response")
        
        validated_questions = []
        for idx, question in enumerate(questions, 1):
            if not isinstance(question, dict):
                raise ValidationError(f"Question {idx} is not a dictionary")
            
            prompt = question.get('prompt', '').strip()
            if not prompt:
                raise ValidationError(f"Question {idx} missing 'prompt' field")
            
            if 'category' not in question or not question.get('category'):
                raise ValidationError(f"Question {idx} missing 'category' field")
            category = cls.normalize_category(question.get('category'))
            if category not in cls.VALID_CATEGORIES:
                raise ValidationError(f"Question {idx} has invalid category: {question.get('category')}")

            if 'difficulty' not in question or not question.get('difficulty'):
                raise ValidationError(f"Question {idx} missing 'difficulty' field")
            difficulty = cls.normalize_difficulty(question.get('difficulty'))
            if difficulty not in {'easy', 'medium', 'hard'}:
                raise ValidationError(f"Question {idx} has invalid difficulty: {question.get('difficulty')}")
            
            if 'evaluation_criteria' not in question:
                raise ValidationError(f"Question {idx} missing 'evaluation_criteria' field")
            criteria = question.get('evaluation_criteria')
            if isinstance(criteria, dict):
                criteria = list(criteria.keys()) if criteria else []
            if not isinstance(criteria, list) or not criteria:
                raise ValidationError(f"Question {idx} has invalid 'evaluation_criteria'; must be non-empty list")
            
            expected_elements = question.get('expected_answer_elements', [])
            if not isinstance(expected_elements, list):
                expected_elements = []

            if 'order' not in question:
                raise ValidationError(f"Question {idx} missing 'order' field")
            try:
                order_val = int(question.get('order'))
                if order_val <= 0:
                    raise ValidationError(f"Question {idx} has invalid 'order' (must be positive integer)")
            except (ValueError, TypeError):
                raise ValidationError(f"Question {idx} has invalid 'order' (must be integer)")
            
            validated_question = {
                'prompt': prompt,
                'category': category,
                'difficulty': difficulty,
                'evaluation_criteria': criteria or [],
                'expected_answer_elements': expected_elements or [],
                'order': order_val,
                'request_id': question.get('request_id', f'ai-{idx}'),
            }
            
            validated_questions.append(validated_question)
        
        return validated_questions

    @classmethod
    def validate_question(cls, question):
        """Validate a single question dict."""
        validated = cls.validate({'questions': [question]})
        return validated[0]

    @classmethod
    def validate_batch(cls, questions):
        """Validate a batch (list) of question dicts."""
        return cls.validate({'questions': questions})

    @classmethod
    def validate_response(cls, parsed_response):
        """Validate a full parsed response."""
        return cls.validate(parsed_response)


class AIConnector:
    """
    AI service connector using Mistral SDK (same as assessments).
    Falls back to Groq when Mistral fails or quota is hit.
    """
    
    def __init__(self):
        # Initialize Mistral client (same as assessments)
        self.mistral_api_key = (
            getattr(settings, 'INTERVIEW_PRACTICE_MISTRAL_API_KEY', None)
            or getattr(settings, 'MISTRAL_AI_API_KEY', '')
        )
        self.mistral_model = (
            getattr(settings, 'INTERVIEW_PRACTICE_MISTRAL_MODEL', None)
            or getattr(settings, 'MISTRAL_AI_MODEL', 'mistral-small-latest')
        )
        
        self.mistral_client = None
        if Mistral and self.mistral_api_key:
            try:
                self.mistral_client = Mistral(api_key=self.mistral_api_key)
                logger.info("Mistral client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Mistral client: {e}")
        
        # Initialize Groq client (fallback)
        self.groq_api_key = getattr(settings, 'GROQ_API_KEY', '')
        self.groq_model = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
        
        self.groq_client = None
        if Groq and self.groq_api_key:
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
                logger.info("Groq client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")

    def generate_questions(self, session):
        """
        Generate practice interview questions using Mistral SDK first, then Gemini fallback.
        """
        prompt = self._build_context_prompt(session)
        logger.info(f"Generated prompt for session {session.id}: {prompt[:200]}...")
        
        # Try Mistral first (using SDK like assessments)
        if self.mistral_client:
            start_time = time.time()
            try:
                logger.info(f"Attempting Mistral API call for session {session.id}")
                
                response = self.mistral_client.chat.complete(
                    model=self.mistral_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert interview question generator. Generate high-quality, realistic interview questions in valid JSON format."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                
                # Extract content (same as assessments)
                content = ''
                choices = getattr(response, 'choices', [])
                if choices:
                    first_choice = choices[0]
                    message = getattr(first_choice, 'message', None)
                    if message:
                        content = getattr(message, 'content', '')
                
                if content:
                    mistral_latency = time.time() - start_time
                    logger.info(f"Mistral response received for session {session.id} (latency: {mistral_latency:.2f}s)")
                    
                    try:
                        questions, raw_data = self._parse_and_validate_questions(content)
                        if questions:
                            logger.info(
                                f"Successfully generated {len(questions)} questions using Mistral "
                                f"(latency: {mistral_latency:.2f}s, session_id: {session.id})"
                            )
                            for q in questions:
                                q['model_used'] = 'mistral'
                            return questions, raw_data, 'mistral'
                    except Exception as e:
                        logger.warning(f"Failed to parse/validate Mistral response: {e}")
                        
            except Exception as e:
                logger.error(f"Mistral generation failed: {e}", exc_info=True)
        else:
            logger.warning("Mistral client not available")
        
        # Fall back to Groq (only if Mistral fails)
        logger.warning("Mistral generation failed or returned empty. Attempting Groq fallback.")
        
        if self.groq_client is None:
            error_msg = "Error: Both Mistral and Groq AI are unavailable. No API keys configured."
            logger.error(error_msg)
            return [], error_msg, None
        
        try:
            start_time = time.time()
            groq_response = self._generate_questions_groq(prompt)
            groq_latency = time.time() - start_time
            
            if groq_response and not groq_response.startswith("Error:"):
                questions, raw_data = self._parse_and_validate_questions(groq_response)
                if questions:
                    logger.info(
                        f"Successfully generated {len(questions)} questions using Groq fallback "
                        f"(latency: {groq_latency:.2f}s, session_id: {session.id})"
                    )
                    for q in questions:
                        q['model_used'] = 'groq'
                    return questions, raw_data, 'groq'
        except Exception as e:
            logger.error(f"Groq fallback also failed: {e}")
        
        error_msg = "Error: All AI generation attempts failed (Mistral and Groq). Cannot generate questions."
        logger.error(error_msg)
        return [], error_msg, None
    
    def _build_context_prompt(self, session):
        """Build a rich prompt with full context."""
        interview_type = session.interview_type or 'General'
        difficulty = session.difficulty or 'Intermediate'
        focus_area = session.focus_area or 'general topics'
        num_questions = getattr(session, 'number_of_questions', 5) or 5
        
        job_title = ''
        job_description = ''
        if session.application and session.application.job:
            job = session.application.job
            job_title = job.title or ''
            job_description = job.description or ''
        
        candidate_skills = []
        if session.application and session.application.applicant:
            applicant = session.application.applicant
            if hasattr(applicant, 'personal_profile') and applicant.personal_profile:
                profile = applicant.personal_profile
                skills = profile.skills or []
                if isinstance(skills, list):
                    candidate_skills = [
                        s.get('skill') if isinstance(s, dict) else s 
                        for s in skills if s
                    ][:10]
        
        prompt_parts = [
            "Generate exactly the specified number of practice interview questions in valid JSON format.",
            f"\nCandidate Interview Type: {interview_type}",
            f"Difficulty Level: {difficulty}",
            f"Focus Area: {focus_area}",
            f"Number of Questions: {num_questions}",
        ]
        
        if job_title:
            prompt_parts.append(f"\nJob Position: {job_title}")
        
        if job_description:
            desc_preview = job_description[:500]
            if len(job_description) > 500:
                desc_preview += "..."
            prompt_parts.append(f"\nJob Description Summary:\n{desc_preview}")
        
        if candidate_skills:
            skills_str = ', '.join(candidate_skills)
            prompt_parts.append(f"\nCandidate Skills: {skills_str}")
        
        prompt_parts.extend([
            "\n\nRespond with ONLY valid JSON (no markdown, no extra text) following this exact schema:",
            """
{
  "questions": [
    {
      "prompt": "The interview question as a string",
      "category": "behavioral|technical|situational",
      "difficulty": "easy|medium|hard",
      "evaluation_criteria": ["criterion1", "criterion2", "criterion3"],
      "order": 1,
      "expected_answer_elements": ["element1", "element2"]
    }
  ]
}
""",
            f"\nGenerate exactly {num_questions} questions. Ensure variety in categories and difficulty levels.",
            "Tailor questions to the job position and candidate skills when provided.",
            "Return ONLY the JSON object, no other text or markdown formatting."
        ])
        
        return ''.join(prompt_parts)
    
    def _parse_and_validate_questions(self, response_text):
        """Parse and validate JSON questions from response text."""
        if not response_text or response_text.startswith("Error:"):
            raise ValidationError(f"Invalid response: {response_text[:100]}")
        
        # Remove markdown if present (same as assessments)
        content = response_text.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse JSON: {content[:100]}...")
            raise ValidationError(f"Invalid JSON format: {e}")
        
        validated_questions = QuestionValidator.validate(parsed)
        return validated_questions, content

    def _generate_questions_groq(self, prompt):
        """Generate questions using Groq API with retry logic."""
        if not self.groq_client:
            return "Error: Groq not configured"
        
        # Attempt with retries (max 3 times)
        for attempt in range(3):
            try:
                response = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert interview question generator. Generate high-quality, realistic interview questions in valid JSON format."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    response_format={"type": "json_object"}
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                error_msg = str(e)
                
                # Check for rate limiting
                if '429' in error_msg or 'rate_limit' in error_msg.lower():
                    wait_time = (attempt + 1) * 10  # Wait 10s, then 20s, then 30s
                    logger.warning(f"Groq rate limit hit. Sleeping {wait_time}s...")
                    time.sleep(wait_time)
                    continue  # Retry
                
                logger.error(f"Groq API Error: {e}")
                break  # Move on if it's a different error
        
        return "Error: All Groq attempts exhausted after retries"

    def score_response(self, question_prompt, answer_text, evaluation_criteria, video_metrics=None):
        """Score a candidate response using AI."""
        prompt = self._build_scoring_prompt(
            question_prompt,
            answer_text,
            evaluation_criteria,
            video_metrics
        )
        
        # Try Mistral first
        if self.mistral_client:
            try:
                response = self.mistral_client.chat.complete(
                    model=self.mistral_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert interview evaluator. Provide objective, constructive scoring."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )
                
                content = ''
                choices = getattr(response, 'choices', [])
                if choices:
                    first_choice = choices[0]
                    message = getattr(first_choice, 'message', None)
                    if message:
                        content = getattr(message, 'content', '')
                
                if content:
                    # Remove markdown
                    content = content.strip()
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.startswith('```'):
                        content = content[3:]
                    if content.endswith('```'):
                        content = content[:-3]
                    content = content.strip()
                    
                    parsed = json.loads(content)
                    scoring_result = ResponseScorer.score_response(parsed, ai_model='mistral')
                    
                    if scoring_result.get('success'):
                        return scoring_result, content, 'mistral'
            except Exception as e:
                logger.warning(f"Mistral scoring failed: {e}")
        
        # Fallback to Groq
        logger.warning("Attempting Groq for scoring")
        
        if not self.groq_client:
            error_msg = "Error: Both Mistral and Groq AI are unavailable for scoring"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}, error_msg, None
        
        try:
            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert interview evaluator. Provide objective, constructive scoring."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            groq_response = response.choices[0].message.content
            parsed = json.loads(groq_response)
            scoring_result = ResponseScorer.score_response(parsed, ai_model='groq')
            
            if scoring_result.get('success'):
                return scoring_result, groq_response, 'groq'
        except Exception as e:
            logger.warning(f"Groq scoring failed: {e}")
        
        error_msg = "Error: All AI scoring attempts failed"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}, error_msg, None

    def _build_scoring_prompt(self, question_prompt, answer_text, evaluation_criteria, video_metrics=None):
        """Build a comprehensive scoring prompt."""
        prompt_parts = [
            "You are an expert interview evaluator. Score the following candidate response:",
            f"\n\nINTERVIEW QUESTION:\n{question_prompt}",
            f"\n\nCANDIDATE ANSWER:\n{answer_text}",
        ]
        
        if evaluation_criteria:
            criteria_str = '\n'.join([f"- {c}" for c in evaluation_criteria])
            prompt_parts.append(f"\n\nEVALUATION CRITERIA:\n{criteria_str}")
        
        if video_metrics:
            prompt_parts.append("\n\nVIDEO ANALYSIS METRICS:")
            prompt_parts.append(f"- Eye contact with camera: {video_metrics.get('averageGazeAtCamera', 'N/A')}%")
            prompt_parts.append(f"- Head stability (roll angle): {video_metrics.get('averageHeadPose', {}).get('roll', 'N/A')}°")
            prompt_parts.append(f"- Speaking percentage: {video_metrics.get('speakingPercentage', 'N/A')}%")
            prompt_parts.append(f"- Blink rate: {video_metrics.get('averageBlinkRate', 'N/A')}/min")
        
        prompt_parts.extend([
            "\n\nProvide a JSON response with ONLY valid JSON (no markdown) with this structure:",
            """
{
  "content_relevance": 0-100,
  "completeness": 0-100,
  "structure_clarity": 0-100,
  "key_points_covered": ["point1", "point2"],
  "eye_contact_percentage": 0-100,
  "head_stability": 0-100,
  "speaking_consistency": 0-100,
  "presence_score": 0-100,
  "strengths": ["strength1", "strength2", "strength3"],
  "improvements": ["improvement1", "improvement2", "improvement3"],
  "overall_feedback": "detailed constructive feedback"
}
""",
            "\nScore each metric objectively. Return ONLY the JSON object."
        ])
        
        return ''.join(prompt_parts)

        return ''.join(prompt_parts)

    def summarize_interview(self, interview_transcript):
        """Summarize interview transcript and identify key moments."""
        prompt = self._build_summary_prompt(interview_transcript)
        
        # Try Mistral first
        if self.mistral_client:
            try:
                response = self.mistral_client.chat.complete(
                    model=self.mistral_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert interviewer assistant. Summarize the interview and identify key insights."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.5,
                    max_tokens=2000
                )
                
                content = getattr(response.choices[0].message, 'content', '')
                if content:
                    # Remove markdown
                    content = content.replace('```json', '').replace('```', '').strip()
                    try:
                        parsed = json.loads(content)
                        return parsed, content, 'mistral'
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                logger.warning(f"Mistral summary failed: {e}")

        # Fallback to Groq
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[
                         {
                            "role": "system",
                            "content": "You are an expert interviewer assistant. Summarize the interview and identify key insights."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.5,
                    max_tokens=2000,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
                parsed = json.loads(content)
                return parsed, content, 'groq'
            except Exception as e:
                logger.error(f"Groq summary failed: {e}")

        return None, "Error: AI unavailable", None

    def _build_summary_prompt(self, transcript):
        return f"""
Analyze the following interview transcript and provide a structured summary.

TRANSCRIPT:
{transcript[:50000]}  # Limit context window

Respond ONLY in JSON format:
{{
  "summary": "High-level summary of the interview...",
  "key_moments": [
    {{"timestamp": "HH:MM:SS", "description": "Moment description", "type": "strength|weakness|insight"}}
  ],
  "strengths": ["..."],
  "areas_for_improvement": ["..."],
  "recommendation": "Strong Hire / Hire / No Hire"
}}
"""
class ReportGenerator:
    """Generates comprehensive practice session reports."""
    
    @staticmethod
    def aggregate_response_scores(responses):
        """Aggregate scores from all responses by category."""
        category_scores = {}
        all_scores = []
        
        for response in responses:
            try:
                question = response.question
                category = getattr(question, 'category', 'general')
                
                score = float(response.overall_score or 0)
                all_scores.append(score)
                
                if category not in category_scores:
                    category_scores[category] = []
                category_scores[category].append(score)
            except Exception as e:
                logger.error(f"Error aggregating response {response.id}: {e}")
        
        category_breakdown = {}
        for category, scores in category_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            category_breakdown[category] = round(avg_score, 2)
        
        return {
            'category_breakdown': category_breakdown,
            'overall_average': round(sum(all_scores) / len(all_scores), 2) if all_scores else 0,
            'min_score': round(min(all_scores), 2) if all_scores else 0,
            'max_score': round(max(all_scores), 2) if all_scores else 0,
            'total_responses': len(responses)
        }


class ResponseScorer:
    """Validates and scores AI-generated scoring responses."""
    
    @staticmethod
    def validate_scoring_response(raw_response):
        """Validate scoring response structure."""
        if not isinstance(raw_response, dict):
            raise ValidationError("Scoring response must be a dictionary")
        
        required_fields = [
            'content_relevance', 'completeness', 'structure_clarity',
            'key_points_covered', 'eye_contact_percentage', 'head_stability',
            'speaking_consistency', 'presence_score', 'strengths',
            'improvements', 'overall_feedback'
        ]
        
        for field in required_fields:
            if field not in raw_response:
                raise ValidationError(f"Missing required field: {field}")
        
        return True
    
    @staticmethod
    def calculate_weighted_scores(raw_response):
        """Calculate weighted scores from raw AI response."""
        content_score = (
            raw_response.get('content_relevance', 0) +
            raw_response.get('completeness', 0) +
            raw_response.get('structure_clarity', 0)
        ) / 3
        
        delivery_score = (
            raw_response.get('structure_clarity', 0) +
            raw_response.get('speaking_consistency', 0)
        ) / 2
        
        presence_metrics = [
            raw_response.get('eye_contact_percentage', 0),
            raw_response.get('head_stability', 0),
            raw_response.get('presence_score', 0)
        ]
        valid_presence_metrics = [m for m in presence_metrics if m is not None]
        presence_score = sum(valid_presence_metrics) / len(valid_presence_metrics) if valid_presence_metrics else 0
        
        overall_score = (
            (content_score * 0.50) +
            (delivery_score * 0.30) +
            (presence_score * 0.20)
        )
        
        return {
            'content_score': round(content_score, 2),
            'delivery_score': round(delivery_score, 2),
            'presence_score': round(presence_score, 2),
            'overall_score': round(overall_score, 2)
        }
    
    @staticmethod
    def generate_feedback(raw_response, weighted_scores):
        """Generate specific feedback messages based on scores."""
        feedback = []
        
        overall_score = weighted_scores['overall_score']
        
        if overall_score >= 80:
            feedback.append("Excellent response with strong performance across all areas.")
        elif overall_score >= 60:
            feedback.append("Good response with some areas for improvement.")
        else:
            feedback.append("Response needs substantial revision and practice.")
        
        return feedback
    
    @classmethod
    def score_response(cls, raw_response, ai_model='mistral'):
        """Score a response and return detailed scoring information."""
        try:
            cls.validate_scoring_response(raw_response)
            weighted_scores = cls.calculate_weighted_scores(raw_response)
            feedback = cls.generate_feedback(raw_response, weighted_scores)
            
            strengths = raw_response.get('strengths', [])[:3]
            improvements = raw_response.get('improvements', [])[:3]
            
            return {
                'success': True,
                'content_score': weighted_scores['content_score'],
                'delivery_score': weighted_scores['delivery_score'],
                'presence_score': weighted_scores['presence_score'],
                'overall_score': weighted_scores['overall_score'],
                'strengths': strengths,
                'improvements': improvements,
                'feedback': feedback,
                'overall_feedback': raw_response.get('overall_feedback', ''),
                'key_points_covered': raw_response.get('key_points_covered', []),
                'ai_model': ai_model,
                'request_id': raw_response.get('request_id', 'unknown')
            }
        except ValidationError as e:
            logger.error(f"Scoring validation error: {e}")
            return {'success': False, 'error': str(e)}

    @classmethod
    def analyze_strengths(cls, scoring_result):
        """Return list of strengths from a scoring result dict."""
        if not scoring_result:
            return []
        return scoring_result.get('strengths', [])

    @classmethod
    def analyze_improvements(cls, scoring_result):
        """Return list of improvements from a scoring result dict."""
        if not scoring_result:
            return []
        return scoring_result.get('improvements', [])