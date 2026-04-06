"""
AI-powered resume rewriter with template awareness
Supports both Mistral and Groq LLMs
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple
from django.conf import settings

logger = logging.getLogger(__name__)

# Import LLM clients
try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    Mistral = None
    MISTRAL_AVAILABLE = False
    logger.warning("mistralai package not installed. Run: pip install mistralai")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    Groq = None
    GROQ_AVAILABLE = False
    logger.warning("groq package not installed. Run: pip install groq")


class TemplateAwareRewriter:
    """Rewrite resume content based on template style and tone"""
    
    def __init__(self, llm_provider: str = 'mistral'):
        """
        Initialize rewriter with selected LLM provider
        
        Args:
            llm_provider: 'mistral' or 'groq'
        """
        self.llm_provider = llm_provider
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the selected LLM client"""
        if self.llm_provider == 'mistral':
            if not MISTRAL_AVAILABLE:
                raise ImportError("mistralai package not installed")
            
            api_key = getattr(settings, 'MISTRAL_AI_API_KEY', '')
            if not api_key:
                raise ValueError("MISTRAL_AI_API_KEY not configured in settings")
            
            return Mistral(api_key=api_key)
        
        elif self.llm_provider == 'groq':
            if not GROQ_AVAILABLE:
                raise ImportError("groq package not installed")
            
            api_key = getattr(settings, 'GROQ_API_KEY', '')
            if not api_key:
                raise ValueError("GROQ_API_KEY not configured in settings")
            
            return Groq(api_key=api_key)
        
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    def rewrite_with_template(
        self,
        resume_text: str,
        template: Optional[Any] = None,
        context: Optional[Dict[str, str]] = None
    ) -> Tuple[str, int, float]:
        """
        Rewrite resume content based on template style
        
        Args:
            resume_text: Original resume content
            template: ResumeTemplate instance (optional)
            context: Additional context for rewriting
            
        Returns:
            Tuple of (rewritten_text, tokens_used, processing_time_seconds)
        """
        start_time = time.time()
        
        try:
            # Build prompt with template guidance
            prompt = self._build_template_aware_prompt(resume_text, template, context)
            
            logger.info(f"Starting rewrite with {self.llm_provider}")
            
            # Generate rewrite
            if self.llm_provider == 'mistral':
                result = self._rewrite_with_mistral(prompt)
            else:
                result = self._rewrite_with_groq(prompt)
            
            processing_time = time.time() - start_time
            
            logger.info(
                f"Rewrite completed in {processing_time:.2f}s "
                f"using {result['tokens']} tokens"
            )
            
            return result['text'], result['tokens'], processing_time
        
        except Exception as e:
            logger.error(f"Rewrite failed with {self.llm_provider}: {e}")
            raise
    
    def _build_template_aware_prompt(
        self,
        resume_text: str,
        template: Optional[Any],
        context: Optional[Dict[str, str]]
    ) -> str:
        """Build prompt that incorporates template style guidance"""
        
        context = context or {}
        
        # Base prompt
        prompt = f"""You are an expert resume writer with years of experience crafting compelling, ATS-optimized resumes. Rewrite the following resume content to make it more impactful and professional.

ORIGINAL RESUME:
{resume_text}

"""
        
        # Add template-specific guidance
        if template:
            prompt += f"""TEMPLATE STYLE: {template.name} ({template.get_category_display()})
TONE: {template.get_tone_display()}

WRITING STYLE GUIDE:
{template.writing_style_guide}

SECTION PRIORITIES:
{self._format_section_priorities(template.section_priorities)}

"""
        else:
            prompt += """TEMPLATE: Blank (no specific template)
STYLE: Use a professional, ATS-friendly style with clear structure and strong action verbs.

"""
        
        # Add user context
        if context.get('job_title'):
            prompt += f"TARGET JOB TITLE: {context['job_title']}\n"
        if context.get('industry'):
            prompt += f"INDUSTRY: {context['industry']}\n"
        if context.get('highlights'):
            prompt += f"\nKEY HIGHLIGHTS TO EMPHASIZE:\n{context['highlights']}\n"
        if context.get('metrics_focus'):
            prompt += f"\nMETRICS TO HIGHLIGHT:\n{context['metrics_focus']}\n"
        if context.get('job_description'):
            prompt += f"\nJOB DESCRIPTION TO ALIGN WITH:\n{context['job_description']}\n"
        if context.get('additional_instructions'):
            prompt += f"\nADDITIONAL INSTRUCTIONS:\n{context['additional_instructions']}\n"
        
        prompt += """
REQUIREMENTS:
1. Maintain factual accuracy - do not invent experience, skills, or achievements
2. Match the tone and style specified above
3. Use strong, specific action verbs appropriate for the template style
4. Optimize for ATS (Applicant Tracking Systems) - use industry keywords
5. Keep content concise and impactful - every word should add value
6. Prioritize sections as indicated above
7. Quantify achievements with metrics where possible
8. Use consistent formatting and professional language
9. Return ONLY the rewritten resume content, no explanations or meta-commentary

REWRITTEN RESUME:
"""
        
        return prompt
    
    def _format_section_priorities(self, priorities: Dict[str, str]) -> str:
        """Format section priorities for prompt"""
        if not priorities:
            return "All sections have equal priority"
        
        lines = []
        for section, priority in priorities.items():
            priority_str = str(priority).upper()
            lines.append(f"- {section.title()}: {priority_str} priority")
        
        return "\n".join(lines) if lines else "All sections have equal priority"
    
    def _rewrite_with_mistral(self, prompt: str) -> Dict[str, Any]:
        """Generate rewrite using Mistral AI"""
        model = getattr(settings, 'MISTRAL_AI_MODEL', 'mistral-small-latest')
        
        try:
            response = self.client.chat.complete(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            
            text = response.choices[0].message.content
            tokens = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return {'text': text, 'tokens': tokens}
            
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            raise
    
    def _rewrite_with_groq(self, prompt: str) -> Dict[str, Any]:
        """Generate rewrite using Groq"""
        model = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            
            text = response.choices[0].message.content
            tokens = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return {'text': text, 'tokens': tokens}
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise


class RewriteQualityAnalyzer:
    """Analyze quality of AI-generated rewrites"""
    
    @staticmethod
    def analyze_rewrite(original: str, rewritten: str) -> Dict[str, Any]:
        """
        Analyze quality metrics of rewrite
        
        Args:
            original: Original resume text
            rewritten: Rewritten resume text
            
        Returns:
            Dictionary of quality metrics
        """
        return {
            'original_length': len(original),
            'rewritten_length': len(rewritten),
            'length_change_percent': (
                ((len(rewritten) - len(original)) / len(original)) * 100
                if len(original) > 0 else 0
            ),
            'original_word_count': len(original.split()),
            'rewritten_word_count': len(rewritten.split()),
            'has_bullet_points': '•' in rewritten or '-' in rewritten,
            'has_numbers': any(char.isdigit() for char in rewritten),
        }
    
    @staticmethod
    def extract_action_verbs(text: str) -> list[str]:
        """Extract action verbs from text (simple heuristic)"""
        # Common action verbs in resumes
        action_verbs = {
            'achieved', 'improved', 'developed', 'created', 'managed',
            'led', 'designed', 'implemented', 'increased', 'reduced',
            'built', 'launched', 'optimized', 'streamlined', 'coordinated',
            'executed', 'delivered', 'established', 'initiated', 'spearheaded',
        }
        
        words = text.lower().split()
        found_verbs = [word for word in words if word in action_verbs]
        
        return list(set(found_verbs))
