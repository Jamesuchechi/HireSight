"""
Mistral AI client for enhanced resume screening.

This module provides integration with Mistral Small (Codestral) for:
- Advanced resume parsing
- Intelligent job matching
- Skill gap analysis
- Interview question generation
- Candidate summaries
- Bias detection
"""
import logging
import json
from typing import Dict, List, Optional, Any
from functools import lru_cache
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from django.conf import settings
from django.core.cache import caches
from django.utils import timezone

logger = logging.getLogger(__name__)


class MistralAIError(Exception):
    """Base exception for Mistral AI errors."""
    pass


class MistralAIRateLimitError(MistralAIError):
    """Rate limit exceeded."""
    pass


class MistralAIClient:
    """
    Client for interacting with Mistral AI API.
    
    Features:
    - Automatic retry with exponential backoff
    - Response caching
    - Rate limiting
    - Error handling
    - Fallback support
    """
    
    def __init__(self):
        """Initialize Mistral AI client."""
        self.api_key = getattr(settings, 'MISTRAL_AI_API_KEY', '')
        self.base_url = getattr(settings, 'MISTRAL_AI_BASE_URL', 'https://api.mistral.ai/v1')
        self.model = getattr(settings, 'MISTRAL_AI_MODEL', 'mistral-small-latest')
        self.timeout = getattr(settings, 'MISTRAL_AI_TIMEOUT', 30)
        self.cache = caches['default']
        
        if not self.api_key:
            logger.warning("MISTRAL_AI_API_KEY not configured. AI features will use fallback.")
    
    def _get_cache_key(self, prompt: str, operation: str) -> str:
        """Generate cache key for AI response."""
        import hashlib
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        return f"mistral_ai:{operation}:{prompt_hash}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    def _make_request(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Make request to Mistral AI API with retry logic.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            API response dictionary
        """
        if not self.api_key:
            raise MistralAIError("Mistral AI API key not configured")
        
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
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.3,  # Lower temperature for more consistent results
                        "max_tokens": 2000
                    }
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("Mistral AI rate limit exceeded")
                raise MistralAIRateLimitError("Rate limit exceeded. Please try again later.")
            elif e.response.status_code == 401:
                logger.error("Mistral AI authentication failed")
                raise MistralAIError("Invalid API key")
            else:
                logger.error(f"Mistral AI HTTP error: {e.response.status_code} - {e.response.text}")
                raise MistralAIError(f"API request failed: {e.response.status_code}")
        
        except httpx.TimeoutException:
            logger.error("Mistral AI request timeout")
            raise
        
        except Exception as e:
            logger.error(f"Mistral AI unexpected error: {str(e)}", exc_info=True)
            raise MistralAIError(f"Unexpected error: {str(e)}")
    
    def parse_resume(self, resume_text: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Parse resume using Mistral AI.
        
        Args:
            resume_text: Raw resume text
            use_cache: Whether to use cached results
            
        Returns:
            Parsed resume data with structured information
        """
        cache_key = self._get_cache_key(resume_text, 'parse_resume')
        
        # Check cache first
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info("Using cached resume parse result")
                return cached
        
        system_prompt = """You are an expert resume parser. Extract structured information from resumes.
Return ONLY valid JSON with this exact structure (no markdown, no code blocks):
{
    "personal_info": {
        "name": "Full Name",
        "email": "email@example.com",
        "phone": "phone number",
        "location": "city, country"
    },
    "summary": "Professional summary",
    "skills": ["skill1", "skill2", "skill3"],
    "experience": [
        {
            "title": "Job Title",
            "company": "Company Name",
            "duration": "Jan 2020 - Present",
            "description": "Job description",
            "achievements": ["achievement1", "achievement2"]
        }
    ],
    "education": [
        {
            "degree": "Degree Name",
            "institution": "University Name",
            "year": "2020",
            "field": "Field of Study"
        }
    ],
    "certifications": ["cert1", "cert2"],
    "languages": ["language1", "language2"]
}"""
        
        prompt = f"Parse this resume and extract structured information:\n\n{resume_text}"
        
        try:
            response = self._make_request(prompt, system_prompt)
            
            # Extract content from response
            content = response['choices'][0]['message']['content']
            
            # Remove markdown code blocks if present
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            # Parse JSON
            parsed_data = json.loads(content)
            
            # Cache result
            if use_cache:
                self.cache.set(cache_key, parsed_data, timeout=86400)  # Cache for 24 hours
            
            logger.info("Successfully parsed resume with Mistral AI")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing resume with Mistral AI: {str(e)}", exc_info=True)
            raise MistralAIError(f"Resume parsing failed: {str(e)}")
    
    def calculate_match_score(
        self,
        resume_text: str,
        job_description: str,
        required_skills: List[str],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate match score between resume and job using Mistral AI.
        
        Args:
            resume_text: Resume text
            job_description: Job description
            required_skills: List of required skills
            use_cache: Whether to use cached results
            
        Returns:
            Match analysis with score and details
        """
        cache_key = self._get_cache_key(
            f"{resume_text[:500]}{job_description[:500]}",
            'match_score'
        )
        
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info("Using cached match score")
                return cached
        
        system_prompt = """You are an expert recruiter. Analyze how well a candidate matches a job.
Return ONLY valid JSON (no markdown, no code blocks) with this structure:
{
    "overall_score": 85,
    "skills_match": {
        "matched": ["skill1", "skill2"],
        "missing": ["skill3"],
        "score": 80
    },
    "experience_match": {
        "relevant_years": 5,
        "score": 90,
        "explanation": "Strong relevant experience"
    },
    "education_match": {
        "meets_requirements": true,
        "score": 85
    },
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1"],
    "recommendation": "Strong candidate",
    "detailed_analysis": "Comprehensive analysis..."
}"""
        
        prompt = f"""Analyze this candidate for the job:

JOB DESCRIPTION:
{job_description}

REQUIRED SKILLS:
{', '.join(required_skills)}

CANDIDATE RESUME:
{resume_text}

Provide a detailed match analysis."""
        
        try:
            response = self._make_request(prompt, system_prompt)
            content = response['choices'][0]['message']['content']
            
            # Clean response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            match_data = json.loads(content)
            
            # Cache result
            if use_cache:
                self.cache.set(cache_key, match_data, timeout=3600)  # 1 hour
            
            logger.info(f"Calculated match score: {match_data.get('overall_score', 0)}%")
            return match_data
            
        except Exception as e:
            logger.error(f"Error calculating match score: {str(e)}", exc_info=True)
            raise MistralAIError(f"Match calculation failed: {str(e)}")
    
    def generate_interview_questions(
        self,
        job_title: str,
        required_skills: List[str],
        experience_level: str,
        num_questions: int = 10
    ) -> List[Dict[str, str]]:
        """
        Generate interview questions for a job role.
        
        Args:
            job_title: Job title
            required_skills: Required skills
            experience_level: Experience level (junior/mid/senior)
            num_questions: Number of questions to generate
            
        Returns:
            List of interview questions with categories
        """
        system_prompt = """You are an expert interviewer. Generate relevant interview questions.
Return ONLY valid JSON array (no markdown) with this structure:
[
    {
        "question": "Question text",
        "category": "technical/behavioral/situational",
        "difficulty": "easy/medium/hard",
        "skill": "related skill"
    }
]"""
        
        prompt = f"""Generate {num_questions} interview questions for:

Job Title: {job_title}
Required Skills: {', '.join(required_skills)}
Experience Level: {experience_level}

Include a mix of technical, behavioral, and situational questions."""
        
        try:
            response = self._make_request(prompt, system_prompt)
            content = response['choices'][0]['message']['content']
            
            # Clean response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            questions = json.loads(content)
            
            logger.info(f"Generated {len(questions)} interview questions")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating interview questions: {str(e)}", exc_info=True)
            raise MistralAIError(f"Question generation failed: {str(e)}")
    
    def generate_candidate_summary(
        self,
        resume_text: str,
        match_score: int,
        strengths: List[str],
        weaknesses: List[str]
    ) -> str:
        """
        Generate executive summary of candidate.
        
        Args:
            resume_text: Resume text
            match_score: Match score
            strengths: Candidate strengths
            weaknesses: Candidate weaknesses
            
        Returns:
            Executive summary text
        """
        system_prompt = """You are a professional recruiter writing executive summaries.
Create a concise, professional summary (150-200 words) highlighting key points."""
        
        prompt = f"""Create an executive summary for this candidate:

MATCH SCORE: {match_score}%

STRENGTHS:
{chr(10).join(f'- {s}' for s in strengths)}

AREAS FOR DEVELOPMENT:
{chr(10).join(f'- {w}' for w in weaknesses)}

RESUME:
{resume_text[:1000]}

Write a professional summary suitable for hiring managers."""
        
        try:
            response = self._make_request(prompt, system_prompt)
            summary = response['choices'][0]['message']['content'].strip()
            
            logger.info("Generated candidate summary")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}", exc_info=True)
            raise MistralAIError(f"Summary generation failed: {str(e)}")
    
    def detect_bias(
        self,
        job_description: str,
        screening_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect potential biases in job description and screening criteria.
        
        Args:
            job_description: Job description text
            screening_criteria: Screening criteria
            
        Returns:
            Bias analysis with recommendations
        """
        system_prompt = """You are a diversity and inclusion expert. Analyze for potential biases.
Return ONLY valid JSON (no markdown) with this structure:
{
    "bias_score": 75,
    "issues": [
        {
            "type": "age/gender/cultural",
            "severity": "low/medium/high",
            "description": "Issue description",
            "suggestion": "How to improve"
        }
    ],
    "inclusive_score": 80,
    "recommendations": ["recommendation1", "recommendation2"]
}"""
        
        prompt = f"""Analyze this job posting for potential biases:

JOB DESCRIPTION:
{job_description}

SCREENING CRITERIA:
{json.dumps(screening_criteria, indent=2)}

Identify any age, gender, cultural, or other biases. Provide specific suggestions."""
        
        try:
            response = self._make_request(prompt, system_prompt)
            content = response['choices'][0]['message']['content']
            
            # Clean response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            bias_data = json.loads(content)
            
            logger.info(f"Bias analysis complete. Score: {bias_data.get('bias_score', 0)}")
            return bias_data
            
        except Exception as e:
            logger.error(f"Error detecting bias: {str(e)}", exc_info=True)
            raise MistralAIError(f"Bias detection failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Mistral AI is available and configured."""
        return bool(self.api_key)


# Singleton instance
mistral_client = MistralAIClient()