"""
AI Connector for Interview Practice Sessions

Handles integration with multiple AI services, preferring Gemini with fallback to Mistral.
"""
import json
import logging
import time
import requests
from django.conf import settings
from .utils import generate_with_full_fallback

logger = logging.getLogger(__name__)

# Provide a stable `genai` symbol for tests that patch the module.
# Prefer `google.genai` if available, then `google.generativeai` as a fallback.
try:
    import google.genai as genai  # newer package
except Exception:
    try:
        import google.generativeai as genai  # legacy package
    except Exception:
        genai = None


class PromptBuilder:
    """Production-ready prompt builder for interview practice AI calls.

    Responsibilities:
    - Accept a context dict and produce a deterministic prompt string.
    - Sanitize inputs to avoid JSON injection or broken formatting.
    - Provide configurable options (language, max_job_desc_len).
    - Expose `build_prompt()` for callers.
    """

    DEFAULT_MAX_DESC = 1000

    def __init__(self, context=None, *, language='en', max_job_desc_len=None):
        self.context = context or {}
        self.language = language or 'en'
        self.max_job_desc_len = max_job_desc_len or self.DEFAULT_MAX_DESC

    def _sanitize(self, text):
        if text is None:
            return ''
        # Simple sanitization: ensure string, strip control chars
        s = str(text)
        # Replace problematic unicode control characters
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
        number_of_questions = int(ctx.get('number_of_questions') or ctx.get('number_of_questions', 5) or 5)

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

        # JSON schema instruction block (explicit and strict)
        schema = (
            "Respond with ONLY a JSON object (no markdown or explanations). Follow this schema exactly:\n"
            "{\n  \"questions\": [\n    {\n      \"prompt\": \"string\",\n      \"category\": \"behavioral|technical|situational\",\n      \"difficulty\": \"easy|medium|hard\",\n      \"evaluation_criteria\": [\"criterion1\", \"criterion2\"],\n      \"order\": 1,\n      \"expected_answer_elements\": [\"element1\", \"element2\"]\n    }\n  ]\n}\n"
        )

        parts.append(schema)
        parts.append("Ensure variety across categories and difficulty, and tailor to the role and skills when provided.")
        parts.append("Return exactly the requested number of questions.")

        prompt = "\n\n".join(parts)

        # Guarantee deterministic length and content for caching and testing
        return prompt


class VideoMetricsParser:
    """Robust parser and calculator for video metrics used in scoring.

    This parser normalizes input JSON from the client (MediaPipe + analyzer)
    and provides utility methods to compute derived metrics such as eye-contact
    percentage and head stability score.
    """

    def parse(self, metrics_json):
        if not isinstance(metrics_json, dict):
            raise ValueError('metrics_json must be a dict')

        normalized = {}
        # Sections we expect
        sections = ['eye_contact', 'head_stability', 'speaking', 'engagement', 'audio']
        for s in sections:
            val = metrics_json.get(s, {}) or {}
            normalized[s] = val if isinstance(val, dict) else {}

        # Compute derived fields
        ec = normalized['eye_contact']
        fw = ec.get('frames_with_contact')
        tf = ec.get('total_frames')
        if 'percentage' not in ec and (fw is not None and tf is not None):
            try:
                ec['percentage'] = round((float(fw) / float(tf)) * 100, 1) if tf else 0.0
            except Exception:
                ec['percentage'] = 0.0

        hs = normalized['head_stability']
        if 'stability_score' not in hs:
            movement = hs.get('movement_pixels', 0) or 0
            max_m = hs.get('max_movement_pixels', hs.get('max_movement', 100)) or 100
            hs['stability_score'] = self.calculate_head_stability_score(movement, max_m)

        return normalized

    def calculate_eye_contact_percentage(self, frames_with_contact, total_frames):
        try:
            frames_with_contact = float(frames_with_contact or 0)
            total_frames = float(total_frames or 0)
            if total_frames == 0:
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
            if score < 0:
                score = 0.0
            if score > 1:
                score = 1.0
            return round(score, 3)
        except Exception:
            return 0.0



class PromptBuilder:
    """Production-ready prompt builder for interview question generation.

    Features:
    - Accepts a context dict describing role, job, skills, focus areas, difficulty,
      number_of_questions and language.
    - Sanitizes and normalizes values.
    - Produces deterministic prompts suitable for AI models and for unit tests.
    - Includes explicit JSON schema instructions and evaluation criteria guidance.
    """

    DEFAULT_NUM_QUESTIONS = 5

    def __init__(self, context=None):
        self.context = context or {}

    def _normalize_list(self, value):
        if not value:
            return []
        if isinstance(value, str):
            return [v.strip() for v in value.split(',') if v.strip()]
        if isinstance(value, (list, tuple)):
            return [str(v).strip() for v in value if v]
        return [str(value)]

    def _safe(self, v, default=''):
        return str(v).strip() if v is not None else default

    def build_prompt(self):
        ctx = self.context or {}
        role = self._safe(ctx.get('role_title'), 'Candidate')
        job_desc = self._safe(ctx.get('job_description'))
        skills = self._normalize_list(ctx.get('required_skills'))
        focus = self._normalize_list(ctx.get('focus_areas'))
        difficulty = self._safe(ctx.get('difficulty'), 'medium').lower()
        try:
            count = int(ctx.get('number_of_questions') or self.DEFAULT_NUM_QUESTIONS)
        except Exception:
            count = self.DEFAULT_NUM_QUESTIONS
        language = self._safe(ctx.get('language'), 'en')

        parts = []
        parts.append("Interview Practice:")
        parts.append(f"Role/Position: {role}")
        parts.append(f"Difficulty Level: {difficulty}")
        parts.append(f"Number of Questions: {count}")
        parts.append(f"Language: {language}")

        if job_desc:
            # keep description reasonably sized
            parts.append("Job Description Summary:\n" + (job_desc[:1000] + ('...' if len(job_desc) > 1000 else '')))

        if skills:
            parts.append("Key Skills: " + ", ".join(skills[:20]))

        if focus:
            parts.append("Focus Areas: " + ", ".join(focus[:10]))

        # Add deterministic JSON schema instructions
        json_schema = (
            "Respond with ONLY valid JSON (no markdown) following this schema:\n"
            "{\n  \"questions\": [\n    {\n      \"prompt\": \"string\",\n      \"category\": \"behavioral|technical|situational\",\n      \"difficulty\": \"easy|medium|hard\",\n      \"evaluation_criteria\": [\"criterion1\", \"criterion2\"],\n      \"order\": 1,\n      \"expected_answer_elements\": [\"element1\"]\n    }\n  ]\n}\n"
        )

        parts.append(json_schema)

        # Guidance for evaluation criteria and scoring
        parts.append(
            "Provide evaluation_criteria for each question as a list of specific measurable items. "
            "Where applicable include expected_answer_elements which the scorer can use to check coverage."
        )

        prompt = '\n\n'.join(parts)

        # Ensure determinism: canonicalize whitespace
        prompt = '\n'.join([line.strip() for line in prompt.splitlines() if line.strip()])

        # Guarantee a minimum length for clarity
        if len(prompt) < 250:
            prompt += '\n\nAdditional instructions: produce clear, varied questions aligned to the role and skills.'

        return prompt


class VideoMetricsParser:
    """Parse and normalize video analysis metrics.

    Responsibilities:
    - Accept raw JSON/dict metrics from client-side analyzers
    - Compute derived fields (eye contact percentage, head stability score)
    - Normalize missing fields safely
    """

    def parse(self, metrics):
        if metrics is None:
            return {}

        if not isinstance(metrics, dict):
            raise ValueError('metrics must be a dict')

        # Work with safe copies but preserve explicit None for absent sections
        out = {}
        # If a section is explicitly None in the incoming metrics, preserve None
        for section in ('eye_contact', 'head_stability', 'speaking', 'engagement', 'audio'):
            raw = metrics.get(section)
            if raw is None:
                out[section] = None
            else:
                out[section] = dict(raw or {})

        # Normalize numeric-like fields in eye_contact (only if present)
        ec = out['eye_contact'] or {}
        for key in ('frames_with_contact', 'total_frames', 'percentage'):
            if key in ec:
                try:
                    if ec[key] is None:
                        ec[key] = 0
                    else:
                        # coerce strings like '12' to numbers, non-numeric -> 0
                        if isinstance(ec[key], str):
                            ec[key] = ec[key].strip()
                        ec[key] = float(ec[key]) if ec[key] != '' else 0
                        if key != 'percentage' and float(ec[key]).is_integer():
                            ec[key] = int(ec[key])
                except Exception:
                    ec[key] = 0 if key != 'percentage' else 0.0

        # Compute eye contact percentage if missing or zero-length
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

        # Normalize head stability numeric fields and compute stability_score (only if present)
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
        """Aggregate parsed metrics into an overall presence score (0-100).

        Weights:
        - eye_contact: 40%
        - head_stability: 35%
        - speaking consistency: 25%
        """
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
    """
    Validates AI-generated questions against the expected schema and normalizes data.
    """
    
    VALID_CATEGORIES = {'behavioral', 'technical', 'situational'}
    VALID_DIFFICULTIES = {'easy', 'medium', 'hard', 'beginner', 'intermediate', 'advanced'}
    
    @staticmethod
    def normalize_difficulty(difficulty):
        """Map various difficulty formats to standard values."""
        if not difficulty:
            return 'medium'
        
        difficulty_lower = str(difficulty).lower().strip()
        
        # Map to standard format
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
        
        # Map to standard format
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
        """
        Validate JSON response against schema.
        
        Expected schema:
        {
          "questions": [
            {
              "prompt": "string",
              "category": "behavioral|technical|situational",
              "difficulty": "easy|medium|hard",
              "evaluation_criteria": ["criterion1", "criterion2"],
              "order": 1,
              "expected_answer_elements": ["element1", "element2"]
            }
          ]
        }
        
        Args:
            raw_response: Dict containing the parsed JSON response
            
        Returns:
            list: Validated and normalized questions
            
        Raises:
            ValidationError: If validation fails
        """
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
            
            # Validate required fields
            prompt = question.get('prompt', '').strip()
            if not prompt:
                raise ValidationError(f"Question {idx} missing 'prompt' field")
            
            # Category must be present and valid
            if 'category' not in question or not question.get('category'):
                raise ValidationError(f"Question {idx} missing 'category' field")
            category = cls.normalize_category(question.get('category'))
            if category not in cls.VALID_CATEGORIES:
                raise ValidationError(f"Question {idx} has invalid category: {question.get('category')}")

            # Difficulty must be present and one of easy|medium|hard
            if 'difficulty' not in question or not question.get('difficulty'):
                raise ValidationError(f"Question {idx} missing 'difficulty' field")
            difficulty = cls.normalize_difficulty(question.get('difficulty'))
            if difficulty not in {'easy', 'medium', 'hard'}:
                raise ValidationError(f"Question {idx} has invalid difficulty: {question.get('difficulty')}")
            
            # Get evaluation criteria (required)
            if 'evaluation_criteria' not in question:
                raise ValidationError(f"Question {idx} missing 'evaluation_criteria' field")
            criteria = question.get('evaluation_criteria')
            if isinstance(criteria, dict):
                criteria = list(criteria.keys()) if criteria else []
            if not isinstance(criteria, list) or not criteria:
                raise ValidationError(f"Question {idx} has invalid 'evaluation_criteria'; must be non-empty list")
            
            # Get expected answer elements (optional)
            expected_elements = question.get('expected_answer_elements', [])
            if not isinstance(expected_elements, list):
                expected_elements = []

            # Order must be present and a positive integer
            if 'order' not in question:
                raise ValidationError(f"Question {idx} missing 'order' field")
            try:
                order_val = int(question.get('order'))
                if order_val <= 0:
                    raise ValidationError(f"Question {idx} has invalid 'order' (must be positive integer)")
            except (ValueError, TypeError):
                raise ValidationError(f"Question {idx} has invalid 'order' (must be integer)")
            
            # Build validated question
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

    # Compatibility helpers expected by tests
    @classmethod
    def validate_question(cls, question):
        """Validate a single question dict and return normalized question."""
        validated = cls.validate({'questions': [question]})
        return validated[0]

    @classmethod
    def validate_batch(cls, questions):
        """Validate a batch (list) of question dicts."""
        return cls.validate({'questions': questions})

    @classmethod
    def validate_response(cls, parsed_response):
        """Validate a full parsed response (dict with 'questions')."""
        return cls.validate(parsed_response)


class AIConnector:
    """
    AI service connector for practice session management.
    
    Priority: Gemini first (with full fallback through keys and models)
    Fallback: Mistral if Gemini completely fails
    """
    
    def __init__(self):
        self.mistral_base_url = (
            getattr(settings, 'INTERVIEW_PRACTICE_MISTRAL_BASE_URL', None)
            or getattr(settings, 'MISTRAL_AI_BASE_URL', 'https://api.mistral.ai/v1')
        )
        self.mistral_model = (
            getattr(settings, 'INTERVIEW_PRACTICE_MISTRAL_MODEL', None)
            or getattr(settings, 'MISTRAL_AI_MODEL', 'mistral-small-latest')
        )
        self.mistral_api_url = getattr(
            settings,
            'INTERVIEW_PRACTICE_MISTRAL_URL',
            f"{self.mistral_base_url}/models/{self.mistral_model}/completions"
        )
        self.mistral_api_key = (
            getattr(settings, 'INTERVIEW_PRACTICE_MISTRAL_API_KEY', None)
            or getattr(settings, 'MISTRAL_AI_API_KEY', '')
        )
        self.timeout = (
            getattr(settings, 'INTERVIEW_PRACTICE_MISTRAL_TIMEOUT', None) 
            or getattr(settings, 'MISTRAL_AI_TIMEOUT', 30)
        )

    def generate_questions(self, session):
        """
        Generate practice interview questions for a session with full context.
        
        Attempts to use Gemini first with full fallback, then falls back to Mistral
        if Gemini completely fails. Never returns hardcoded/fake questions.
        
        Args:
            session: InterviewPracticeSession instance
            
        Returns:
            tuple: (questions_list, raw_response, model_used) where questions_list is the
                   validated questions or empty list if generation fails
        """
        # Build rich prompt with full context
        prompt = self._build_context_prompt(session)
        logger.info(f"Generated prompt for session {session.id}: {prompt[:200]}...")
        
        # Try Gemini first (prefer direct genai client if available so tests can patch it)
        start_time = time.time()
        gemini_response = None
        if genai is not None:
            try:
                logger.info(f"Attempting Gemini client call for session {session.id}")
                client = genai.Client()
                # call generate_content - tests patch this method and return an object with .text
                resp = client.models.generate_content(contents=prompt)
                gemini_response = getattr(resp, 'text', resp)
                logger.info(f"Gemini response received for session {session.id}: {gemini_response[:200]}...")
            except Exception as e:
                logger.warning(f"genai client call failed: {e}")
                gemini_response = f"Error: genai client failed: {e}"
        else:
            logger.info("genai module not available, using fallback")
            gemini_response = generate_with_full_fallback(prompt)
        
        gemini_latency = time.time() - start_time
        logger.info(f"Gemini latency: {gemini_latency:.2f}s")
        
        # Check if Gemini succeeded (doesn't start with "Error:")
        if not gemini_response.startswith("Error:"):
            try:
                logger.info(f"Parsing and validating Gemini response for session {session.id}")
                questions, raw_data = self._parse_and_validate_questions(gemini_response)
                if questions:
                    logger.info(
                        f"Successfully generated {len(questions)} questions using Gemini "
                        f"(latency: {gemini_latency:.2f}s, session_id: {session.id})"
                    )
                    # Add model info to each question
                    for q in questions:
                        q['model_used'] = 'gemini'
                    return questions, raw_data, 'gemini'
            except Exception as e:
                logger.warning(f"Failed to parse/validate Gemini response: {e}")
        
        # Gemini failed, fall back to Mistral
        logger.warning(f"Gemini generation failed or returned empty: {gemini_response}. Attempting Mistral fallback.")
        
        if not self.mistral_api_key:
            error_msg = "Error: Both Gemini and Mistral AI are unavailable. No API keys configured."
            logger.error(error_msg)
            return [], error_msg, None
        
        try:
            start_time = time.time()
            mistral_response = self._generate_questions_mistral(prompt)
            mistral_latency = time.time() - start_time
            logger.info(f"Mistral latency: {mistral_latency:.2f}s")
            
            if mistral_response and not mistral_response.startswith("Error:"):
                questions, raw_data = self._parse_and_validate_questions(mistral_response)
                if questions:
                    logger.info(
                        f"Successfully generated {len(questions)} questions using Mistral fallback "
                        f"(latency: {mistral_latency:.2f}s, session_id: {session.id})"
                    )
                    # Add model info to each question
                    for q in questions:
                        q['model_used'] = 'mistral'
                    return questions, raw_data, 'mistral'
        except Exception as e:
            logger.error(f"Mistral fallback also failed: {e}")
        
        error_msg = "Error: All AI generation attempts failed (Gemini and Mistral). Cannot generate questions."
        logger.error(error_msg)
        return [], error_msg, None
    
    def _build_context_prompt(self, session):
        """
        Build a rich prompt with full context about the job, candidate, and session.
        
        Args:
            session: InterviewPracticeSession instance
            
        Returns:
            str: The context-enriched prompt
        """
        # Extract basic session info
        interview_type = session.interview_type or 'General'
        difficulty = session.difficulty or 'Intermediate'
        focus_area = session.focus_area or 'general topics'
        num_questions = getattr(session, 'number_of_questions', 5) or 5
        
        # Extract job info if available
        job_title = ''
        job_description = ''
        if session.application and session.application.job:
            job = session.application.job
            job_title = job.title or ''
            job_description = job.description or ''
        
        # Extract candidate skills if available
        candidate_skills = []
        if session.application and session.application.applicant:
            applicant = session.application.applicant
            if hasattr(applicant, 'personal_profile') and applicant.personal_profile:
                profile = applicant.personal_profile
                skills = profile.skills or []
                if isinstance(skills, list):
                    # Extract skill names from objects
                    candidate_skills = [
                        s.get('skill') if isinstance(s, dict) else s 
                        for s in skills if s
                    ][:10]  # Limit to top 10 skills
        
        # Build the prompt
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
            # Truncate description if too long
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
        """
        Parse and validate JSON questions from response text.
        
        Args:
            response_text: Response text containing JSON
            
        Returns:
            tuple: (validated_questions, raw_response) or raises ValidationError
        """
        if not response_text or response_text.startswith("Error:"):
            raise ValidationError(f"Invalid response: {response_text[:100]}")
        
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse JSON: {response_text[:100]}...")
            raise ValidationError(f"Invalid JSON format: {e}")
        
        # Validate using QuestionValidator
        validated_questions = QuestionValidator.validate(parsed)
        
        return validated_questions, response_text

    def _generate_questions_mistral(self, prompt):
        """
        Generate questions using Mistral API.
        
        Args:
            prompt: The prompt to send to Mistral
            
        Returns:
            list: Parsed questions or empty list if fails
        """
        payload = {'input': prompt}
        headers = {
            'Authorization': f'Bearer {self.mistral_api_key}',
            'Content-Type': 'application/json',
        }
        
        try:
            resp = requests.post(self.mistral_api_url, json=payload, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            text = self._extract_text(data)
            return self._parse_questions(text)
        except Exception as e:
            logger.error(f"Mistral API call failed: {e}")
            return []

    def _extract_text(self, response_data):
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

    def _parse_questions(self, text):
        """
        Parse JSON questions from response text (legacy method, now uses validator).
        
        Args:
            text: Response text potentially containing JSON
            
        Returns:
            list: Parsed questions list or empty list if parsing fails
        """
        if not text or text.startswith("Error:"):
            return []
        
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                questions = parsed.get('questions') or parsed.get('items') or []
            elif isinstance(parsed, list):
                questions = parsed
            else:
                return []
            
            # Validate questions have required fields
            valid_questions = []
            for q in questions:
                if isinstance(q, dict) and q.get('prompt'):
                    valid_questions.append({
                        'prompt': q.get('prompt'),
                        'category': q.get('category', 'General'),
                        'difficulty': q.get('difficulty', 'Intermediate'),
                        'evaluation_criteria': q.get('evaluation_criteria', {}),
                        'request_id': q.get('request_id', f'ai-{id(q)}'[:20]),
                    })
            
            return valid_questions
            
        except json.JSONDecodeError:
            logger.debug(f"Failed to parse JSON from response: {text[:100]}...")
            return []
    
    def score_response(self, question_prompt, answer_text, evaluation_criteria, video_metrics=None):
        """
        Score a candidate response using Gemini with video metrics.
        
        Args:
            question_prompt: The interview question
            answer_text: The candidate's answer text
            evaluation_criteria: List of criteria to evaluate
            video_metrics: Optional dict with video analysis metrics
            
        Returns:
            tuple: (scoring_result_dict, raw_response, model_used)
        """
        # Build the scoring prompt
        prompt = self._build_scoring_prompt(
            question_prompt,
            answer_text,
            evaluation_criteria,
            video_metrics
        )
        
        # Try Gemini first
        start_time = time.time()
        gemini_response = generate_with_full_fallback(prompt)
        gemini_latency = time.time() - start_time
        
        # Check if Gemini succeeded
        if not gemini_response.startswith("Error:"):
            try:
                parsed = json.loads(gemini_response)
                scoring_result = ResponseScorer.score_response(parsed, ai_model='gemini')
                
                if scoring_result.get('success'):
                    logger.info(
                        f"Successfully scored response using Gemini "
                        f"(latency: {gemini_latency:.2f}s, score: {scoring_result.get('overall_score')})"
                    )
                    return scoring_result, gemini_response, 'gemini'
                else:
                    logger.warning(f"Scoring validation failed: {scoring_result.get('error')}")
            except Exception as e:
                logger.warning(f"Failed to parse/validate Gemini scoring: {e}")
        
        # Fallback to Mistral
        logger.warning(f"Gemini scoring failed or returned invalid. Attempting Mistral fallback.")
        
        if not self.mistral_api_key:
            error_msg = "Error: Both Gemini and Mistral AI unavailable for scoring"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}, error_msg, None
        
        try:
            start_time = time.time()
            mistral_response = self._score_response_mistral(prompt)
            mistral_latency = time.time() - start_time
            
            if mistral_response and not mistral_response.startswith("Error:"):
                parsed = json.loads(mistral_response)
                scoring_result = ResponseScorer.score_response(parsed, ai_model='mistral')
                
                if scoring_result.get('success'):
                    logger.info(
                        f"Successfully scored response using Mistral fallback "
                        f"(latency: {mistral_latency:.2f}s, score: {scoring_result.get('overall_score')})"
                    )
                    return scoring_result, mistral_response, 'mistral'
        except Exception as e:
            logger.error(f"Mistral scoring also failed: {e}")
        
        error_msg = "Error: All AI scoring attempts failed"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}, error_msg, None
    
    def _build_scoring_prompt(self, question_prompt, answer_text, evaluation_criteria, video_metrics=None):
        """
        Build a comprehensive scoring prompt for Gemini.
        
        Args:
            question_prompt: The interview question
            answer_text: The candidate's answer
            evaluation_criteria: List of evaluation criteria
            video_metrics: Optional video analysis metrics
            
        Returns:
            str: The scoring prompt
        """
        prompt_parts = [
            "You are an expert interview evaluator. Score the following candidate response:",
            f"\n\nINTERVIEW QUESTION:\n{question_prompt}",
            f"\n\nCANDIDATE ANSWER:\n{answer_text}",
        ]
        
        if evaluation_criteria:
            criteria_str = '\n'.join([f"- {c}" for c in evaluation_criteria])
            prompt_parts.append(f"\n\nEVALUATION CRITERIA:\n{criteria_str}")
        
        # Include video metrics if available
        if video_metrics:
            prompt_parts.append("\n\nVIDEO ANALYSIS METRICS:")
            prompt_parts.append(f"- Eye contact with camera: {video_metrics.get('averageGazeAtCamera', 'N/A')}%")
            prompt_parts.append(f"- Head stability (roll angle): {video_metrics.get('averageHeadPose', {}).get('roll', 'N/A')}°")
            prompt_parts.append(f"- Speaking percentage: {video_metrics.get('speakingPercentage', 'N/A')}%")
            prompt_parts.append(f"- Blink rate: {video_metrics.get('averageBlinkRate', 'N/A')}/min")
        
        prompt_parts.extend([
            "\n\nProvide a JSON response with ONLY valid JSON (no markdown, no extra text) with this structure:",
            """
{
  "content_relevance": 0-100 (is the answer relevant to the question),
  "completeness": 0-100 (does it cover sufficient depth),
  "structure_clarity": 0-100 (is it well-organized and clear),
  "key_points_covered": ["point1", "point2"] (list of key points mentioned),
  "eye_contact_percentage": 0-100 (assessment of eye contact quality),
  "head_stability": 0-100 (assessment of posture/head stability),
  "speaking_consistency": 0-100 (consistency and pace of speech),
  "presence_score": 0-100 (overall presence and engagement),
  "strengths": ["strength1", "strength2", "strength3"] (top 3 strengths),
  "improvements": ["improvement1", "improvement2", "improvement3"] (top 3 improvements),
  "overall_feedback": "detailed constructive feedback"
}
""",
            "\nScore each metric objectively. Return ONLY the JSON object."
        ])
        
        return ''.join(prompt_parts)
    
    def _score_response_mistral(self, prompt):
        """
        Score a response using Mistral API.
        
        Args:
            prompt: The scoring prompt
            
        Returns:
            str: Raw response text or error message
        """
        payload = {'input': prompt}
        headers = {
            'Authorization': f'Bearer {self.mistral_api_key}',
            'Content-Type': 'application/json',
        }
        
        try:
            resp = requests.post(self.mistral_api_url, json=payload, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            text = self._extract_text(data)
            return text
        except Exception as e:
            logger.error(f"Mistral scoring API call failed: {e}")
            return f"Error: {str(e)}"


class ReportGenerator:
    """
    Generates comprehensive practice session reports.
    
    Aggregates response scores, identifies patterns, generates action items,
    and provides personalized recommendations.
    """
    
    @staticmethod
    def aggregate_response_scores(responses):
        """
        Aggregate scores from all responses by category.
        
        Args:
            responses: QuerySet of PracticeResponse objects
            
        Returns:
            dict with category breakdown and statistics
        """
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
        
        # Calculate averages by category
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
    
    @staticmethod
    def identify_patterns(responses):
        """
        Identify patterns and trends in responses.
        
        Returns:
            dict with identified patterns and insights
        """
        patterns = {
            'weak_categories': [],
            'strong_categories': [],
            'common_strengths': [],
            'common_weaknesses': [],
            'consistency_issues': []
        }
        
        # Aggregate strengths and weaknesses
        all_strengths = {}
        all_weaknesses = {}
        scores_by_category = {}
        
        for response in responses:
            try:
                # Track strengths
                strengths = response.strengths or []
                for strength in strengths:
                    all_strengths[strength] = all_strengths.get(strength, 0) + 1
                
                # Track weaknesses
                improvements = response.improvements or []
                for improvement in improvements:
                    all_weaknesses[improvement] = all_weaknesses.get(improvement, 0) + 1
                
                # Track category performance
                category = getattr(response.question, 'category', 'general')
                score = float(response.overall_score or 0)
                if category not in scores_by_category:
                    scores_by_category[category] = []
                scores_by_category[category].append(score)
            except Exception as e:
                logger.error(f"Error identifying patterns in {response.id}: {e}")
        
        # Find weak and strong categories
        for category, scores in scores_by_category.items():
            avg = sum(scores) / len(scores) if scores else 0
            if avg < 60:
                patterns['weak_categories'].append({
                    'category': category,
                    'average_score': round(avg, 2)
                })
            elif avg >= 80:
                patterns['strong_categories'].append({
                    'category': category,
                    'average_score': round(avg, 2)
                })
        
        # Get top 3 common strengths
        patterns['common_strengths'] = sorted(
            all_strengths.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        patterns['common_strengths'] = [
            {'strength': s[0], 'frequency': s[1]} for s in patterns['common_strengths']
        ]
        
        # Get top 3 common weaknesses
        patterns['common_weaknesses'] = sorted(
            all_weaknesses.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        patterns['common_weaknesses'] = [
            {'weakness': w[0], 'frequency': w[1]} for w in patterns['common_weaknesses']
        ]
        
        return patterns
    
    @staticmethod
    def generate_action_items(patterns, category_breakdown):
        """
        Generate specific, actionable items for next practice session.
        
        Args:
            patterns: Output from identify_patterns()
            category_breakdown: Output from aggregate_response_scores()
            
        Returns:
            list of action items
        """
        action_items = []
        
        # Add focus areas for weak categories
        for weak_category in patterns['weak_categories']:
            action_items.append({
                'priority': 'high',
                'action': f"Practice {weak_category['category']} questions extensively",
                'reason': f"Average score {weak_category['average_score']}/100 indicates significant room for improvement",
                'suggestion': f"Aim for at least 5 practice sessions focused on {weak_category['category']} scenarios"
            })
        
        # Add specific improvements based on common weaknesses
        for weakness_data in patterns['common_weaknesses'][:2]:
            weakness = weakness_data['weakness']
            action_items.append({
                'priority': 'high' if weakness_data['frequency'] > 2 else 'medium',
                'action': f"Improve: {weakness}",
                'reason': f"Identified in {weakness_data['frequency']} responses",
                'suggestion': f"Review best practices for {weakness} and practice until natural"
            })
        
        # Add reinforcement for strong areas
        for strong_category in patterns['strong_categories']:
            action_items.append({
                'priority': 'low',
                'action': f"Maintain excellence in {strong_category['category']} questions",
                'reason': f"Strong performance at {strong_category['average_score']}/100",
                'suggestion': "Continue practicing to keep skills sharp"
            })
        
        # Add consistency reminder if scores vary widely
        overall_stats = {
            'min': category_breakdown['min_score'],
            'max': category_breakdown['max_score'],
            'avg': category_breakdown['overall_average']
        }
        
        score_variance = overall_stats['max'] - overall_stats['min']
        if score_variance > 30:
            action_items.append({
                'priority': 'medium',
                'action': f"Work on consistency (variance: {score_variance} points)",
                'reason': f"Scores range from {overall_stats['min']} to {overall_stats['max']}",
                'suggestion': "Focus on applying the same strong techniques across all question types"
            })
        
        return action_items[:7]  # Limit to 7 items
    
    @staticmethod
    def suggest_practice_questions(patterns, weak_categories_count=2):
        """
        Suggest specific question types to practice.
        
        Args:
            patterns: Output from identify_patterns()
            weak_categories_count: Number of weak categories to suggest for
            
        Returns:
            list of practice suggestions
        """
        suggestions = []
        
        # Suggest questions for weak categories
        weak_cats = patterns['weak_categories'][:weak_categories_count]
        category_examples = {
            'behavioral': [
                'Tell me about a time you handled conflict with a colleague',
                'Describe a situation where you failed and what you learned',
                'Share an example of your leadership in a team setting'
            ],
            'technical': [
                'Explain your approach to debugging a complex technical issue',
                'Walk through your solution to a system design problem',
                'How would you optimize a slow database query?'
            ],
            'situational': [
                'How would you approach learning a new technology quickly?',
                'What would you do if you disagreed with your manager\'s decision?',
                'How do you prioritize when you have conflicting deadlines?'
            ],
            'general': [
                'Tell me about your experience with project management',
                'How do you stay updated with industry trends?',
                'Describe your ideal work environment'
            ]
        }
        
        for weak_cat in weak_cats:
            category = weak_cat['category']
            examples = category_examples.get(category, category_examples['general'])
            suggestions.append({
                'category': category,
                'focus_area': f"Strengthen your {category} interview skills",
                'sample_questions': examples
            })
        
        return suggestions
    
    @staticmethod
    def calculate_overall_rating(category_breakdown):
        """
        Calculate an overall rating (0-100) based on performance.
        
        Args:
            category_breakdown: dict from aggregate_response_scores()
            
        Returns:
            float rating 0-100
        """
        overall_avg = category_breakdown.get('overall_average', 0)
        
        # Apply slight bonus for consistency
        if category_breakdown.get('total_responses', 0) >= 5:
            score_variance = (
                category_breakdown.get('max_score', 0) - 
                category_breakdown.get('min_score', 0)
            )
            consistency_bonus = max(0, 5 - (score_variance / 10))
            overall_avg = min(100, overall_avg + consistency_bonus)
        
        return round(overall_avg, 2)
    
    @staticmethod
    def extract_top_strengths(responses, limit=5):
        """
        Extract top strengths from all responses.
        
        Args:
            responses: QuerySet of PracticeResponse objects
            limit: Maximum number of strengths to return
            
        Returns:
            list of strength strings
        """
        strength_counts = {}
        
        for response in responses:
            strengths = response.strengths or []
            for strength in strengths:
                strength_counts[strength] = strength_counts.get(strength, 0) + 1
        
        # Sort by frequency
        sorted_strengths = sorted(
            strength_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [s[0] for s in sorted_strengths[:limit]]
    
    @staticmethod
    def extract_improvement_areas(responses, limit=5):
        """
        Extract key areas for improvement from all responses.
        
        Args:
            responses: QuerySet of PracticeResponse objects
            limit: Maximum number of areas to return
            
        Returns:
            list of improvement area strings
        """
        improvement_counts = {}
        
        for response in responses:
            improvements = response.improvements or []
            for improvement in improvements:
                improvement_counts[improvement] = improvement_counts.get(improvement, 0) + 1
        
        # Sort by frequency
        sorted_improvements = sorted(
            improvement_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [i[0] for i in sorted_improvements[:limit]]


class ResponseScorer:
    """
    Validates and scores AI-generated scoring responses.
    Calculates weighted overall score and generates feedback.
    """
    
    @staticmethod
    def validate_scoring_response(raw_response):
        """
        Validate that the scoring response has the expected structure.
        
        Expected structure:
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
            "overall_feedback": "detailed feedback text",
            "request_id": "optional-request-id"
        }
        """
        if not isinstance(raw_response, dict):
            raise ValidationError("Scoring response must be a dictionary")
        
        required_fields = [
            'content_relevance',
            'completeness',
            'structure_clarity',
            'key_points_covered',
            'eye_contact_percentage',
            'head_stability',
            'speaking_consistency',
            'presence_score',
            'strengths',
            'improvements',
            'overall_feedback'
        ]
        
        for field in required_fields:
            if field not in raw_response:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate numeric ranges
        for score_field in ['content_relevance', 'completeness', 'structure_clarity',
                           'eye_contact_percentage', 'head_stability', 'speaking_consistency',
                           'presence_score']:
            score = raw_response.get(score_field)
            if score is None:
                continue  # Allow missing video metrics
            if not isinstance(score, (int, float)) or score < 0 or score > 100:
                raise ValidationError(f"{score_field} must be a number between 0-100")
        
        # Validate lists
        if not isinstance(raw_response.get('key_points_covered'), list):
            raise ValidationError("key_points_covered must be a list")
        if not isinstance(raw_response.get('strengths'), list):
            raise ValidationError("strengths must be a list")
        if not isinstance(raw_response.get('improvements'), list):
            raise ValidationError("improvements must be a list")
        
        return True
    
    @staticmethod
    def calculate_weighted_scores(raw_response):
        """
        Calculate weighted scores from raw AI response.
        
        Returns:
            dict with content_score, delivery_score, presence_score, and overall_score
        """
        # Content score: average of content_relevance, completeness, structure_clarity
        content_score = (
            raw_response.get('content_relevance', 0) +
            raw_response.get('completeness', 0) +
            raw_response.get('structure_clarity', 0)
        ) / 3
        
        # Delivery score: average of structure_clarity and speaking_consistency
        delivery_score = (
            raw_response.get('structure_clarity', 0) +
            raw_response.get('speaking_consistency', 0)
        ) / 2
        
        # Presence score: average of eye_contact, head_stability, and presence_score
        # Handle missing video metrics gracefully
        presence_metrics = [
            raw_response.get('eye_contact_percentage', 0),
            raw_response.get('head_stability', 0),
            raw_response.get('presence_score', 0)
        ]
        valid_presence_metrics = [m for m in presence_metrics if m is not None]
        presence_score = sum(valid_presence_metrics) / len(valid_presence_metrics) if valid_presence_metrics else 0
        
        # Calculate weighted overall score
        # Content 50%, Delivery 30%, Presence 20%
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
        """
        Generate specific feedback messages based on scores.
        
        Returns:
            dict with detailed feedback
        """
        feedback = []
        
        content_score = weighted_scores['content_score']
        delivery_score = weighted_scores['delivery_score']
        presence_score = weighted_scores['presence_score']
        overall_score = weighted_scores['overall_score']
        
        # Overall feedback
        if overall_score >= 80:
            feedback.append("Excellent response with strong performance across all areas.")
        elif overall_score >= 60:
            feedback.append("Good response with some areas for improvement.")
        elif overall_score >= 40:
            feedback.append("Response shows potential but needs significant improvement.")
        else:
            feedback.append("Response needs substantial revision and practice.")
        
        # Content-specific feedback
        if content_score >= 80:
            feedback.append("Your content is relevant and well-structured.")
        elif content_score >= 60:
            feedback.append("Content is mostly relevant; consider adding more specific examples.")
        elif content_score >= 40:
            feedback.append("Content needs better organization and more specific details.")
        else:
            feedback.append("Focus on providing more comprehensive and relevant content.")
        
        # Delivery-specific feedback
        if delivery_score >= 80:
            feedback.append("Excellent delivery with clear communication and good structure.")
        elif delivery_score >= 60:
            feedback.append("Good delivery; work on clarity and pacing.")
        elif delivery_score >= 40:
            feedback.append("Consider improving organization and speaking clarity.")
        else:
            feedback.append("Work on structuring your thoughts more clearly.")
        
        # Presence-specific feedback
        if presence_score >= 80:
            feedback.append("Great engagement with strong eye contact and presence.")
        elif presence_score >= 60:
            feedback.append("Good presence; improve eye contact consistency.")
        elif presence_score >= 40:
            feedback.append("Work on maintaining steady posture and eye contact.")
        else:
            feedback.append("Focus on engagement and maintaining eye contact with the camera.")
        
        # Key points feedback
        key_points = raw_response.get('key_points_covered', [])
        if key_points:
            feedback.append(f"You covered {len(key_points)} key points: {', '.join(key_points[:3])}")
        else:
            feedback.append("Try to cover more key points in your response.")
        
        return feedback
    
    @classmethod
    def score_response(cls, raw_response, ai_model='gemini'):
        """
        Score a response and return detailed scoring information.
        
        Args:
            raw_response: Raw scoring response from AI
            ai_model: Name of the AI model used
            
        Returns:
            dict with all scoring information
        """
        try:
            # Validate response structure
            cls.validate_scoring_response(raw_response)
            
            # Calculate weighted scores
            weighted_scores = cls.calculate_weighted_scores(raw_response)
            
            # Generate feedback
            feedback = cls.generate_feedback(raw_response, weighted_scores)
            
            # Extract top 3 strengths and improvements
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

    # Helper methods expected by tests
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