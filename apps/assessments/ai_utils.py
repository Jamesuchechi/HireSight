"""
AI-powered question generation using Mistral AI
Place this file in: apps/assessments/ai_utils.py
"""
import json
import logging
from django.conf import settings

try:
    from mistralai import Mistral
except ImportError:
    Mistral = None

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """Generate assessment questions using Mistral AI"""
    
    def __init__(self):
        api_key = getattr(settings, 'MISTRAL_AI_API_KEY', None)
        model = getattr(settings, 'MISTRAL_AI_MODEL', None)
        if not api_key or not model:
            raise ValueError("MISTRAL_AI_API_KEY and MISTRAL_AI_MODEL must be configured")
        if Mistral is None:
            raise ImportError("mistralai library is required for AI question generation")

        self.model = model
        try:
            self.client = Mistral(api_key=api_key)
        except Exception as exc:
            logger.error(f"Failed to initialize Mistral client: {exc}")
            self.client = None
    
    def generate_questions(self, skill_name, difficulty, count=10, question_type='MULTIPLE_CHOICE'):
        """
        Generate questions for a specific skill
        
        Args:
            skill_name: Name of the skill (e.g., "Python", "React")
            difficulty: BEGINNER, INTERMEDIATE, ADVANCED, EXPERT
            count: Number of questions to generate
            question_type: Type of questions (MULTIPLE_CHOICE, TRUE_FALSE, CODE, ESSAY)
        
        Returns:
            List of question dictionaries
        """
        prompt = self._build_prompt(skill_name, difficulty, count, question_type)
        
        if not self.client:
            logger.warning("Mistral client unavailable; skipping question generation")
            return []

        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical assessment creator. Generate high-quality, accurate questions that test real-world knowledge."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000
            )
            content = ''
            choices = getattr(response, 'choices', [])
            if choices:
                first_choice = choices[0]
                message = getattr(first_choice, 'message', None)
                if message:
                    content = getattr(message, 'content', '')
            if not content:
                logger.warning('Mistral response incomplete; no content to parse')
                return []

            questions = self._parse_response(content, question_type)
            logger.info(f"Generated {len(questions)} questions for {skill_name} ({difficulty})")
            return questions

        except AttributeError as exc:
            logger.error(f"Unexpected response format from Mistral: {exc}")
        except Exception as exc:
            logger.error(f"Error generating questions with Mistral AI: {exc}")
        return []
    
    def _build_prompt(self, skill_name, difficulty, count, question_type):
        """Build the prompt for Mistral AI"""
        
        difficulty_descriptions = {
            'BEGINNER': 'basic fundamentals and syntax',
            'INTERMEDIATE': 'practical application and common patterns',
            'ADVANCED': 'complex scenarios and optimization',
            'EXPERT': 'advanced architecture and edge cases'
        }
        
        type_instructions = {
            'MULTIPLE_CHOICE': '''
Generate multiple choice questions with 4 options.
Each option should be plausible but only one correct.
Include detailed explanations for the correct answer.''',
            
            'TRUE_FALSE': '''
Generate true/false questions that test conceptual understanding.
Avoid trick questions. Include explanations.''',
            
            'CODE': '''
Generate coding challenges that require writing actual code.
Include a clear problem statement and expected approach.''',
            
            'ESSAY': '''
Generate open-ended questions that test deep understanding.
Questions should require 2-3 paragraph answers.'''
        }
        
        prompt = f"""Generate {count} {question_type.replace('_', ' ').lower()} questions about {skill_name} at {difficulty} level.

Focus on: {difficulty_descriptions.get(difficulty, 'general knowledge')}

{type_instructions.get(question_type, '')}

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question": "Question text here",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 0,
    "explanation": "Detailed explanation of why this answer is correct",
    "points": 10,
    "estimated_time_seconds": 60
  }}
]

Requirements:
- Questions must be technically accurate and up-to-date
- Avoid outdated practices or deprecated features
- Test practical knowledge, not memorization
- Options should be clearly different and plausible
- Explanations should teach, not just state correctness
- Estimate realistic time based on question complexity

Return ONLY the JSON array, no markdown, no explanations, no additional text."""

        return prompt
    
    def _parse_response(self, content, question_type):
        """Parse Mistral AI response into question dictionaries"""
        try:
            # Remove markdown code blocks if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Parse JSON
            questions = json.loads(content)
            
            # Validate and clean questions
            validated = []
            for q in questions:
                if self._validate_question(q, question_type):
                    validated.append(q)
            
            return validated
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Mistral AI response as JSON: {str(e)}")
            logger.debug(f"Response content: {content[:500]}")
            return []
    
    def _validate_question(self, question, question_type):
        """Validate question structure"""
        required_fields = ['question', 'explanation', 'points', 'estimated_time_seconds']
        
        # Check required fields
        for field in required_fields:
            if field not in question:
                logger.warning(f"Question missing required field: {field}")
                return False
        
        # Type-specific validation
        if question_type == 'MULTIPLE_CHOICE':
            if 'options' not in question or len(question['options']) < 2:
                logger.warning("Multiple choice question needs at least 2 options")
                return False
            if 'correct_answer' not in question:
                logger.warning("Multiple choice question needs correct_answer index")
                return False
        
        elif question_type == 'TRUE_FALSE':
            if 'options' not in question or len(question['options']) != 2:
                question['options'] = ['True', 'False']
            if 'correct_answer' not in question:
                logger.warning("True/false question needs correct_answer")
                return False
        
        return True
    
    def bulk_generate_for_test(self, test):
        """Generate all questions needed for a test"""
        from .models import QuestionPool
        
        questions = self.generate_questions(
            skill_name=test.skill_name,
            difficulty=test.difficulty,
            count=test.question_count,
            question_type='MULTIPLE_CHOICE'
        )
        
        created_count = 0
        for q_data in questions:
            # Create QuestionPool entry
            question = QuestionPool.objects.create(
                skill_name=test.skill_name,
                difficulty=test.difficulty,
                question_type='MULTIPLE_CHOICE',
                question=q_data['question'],
                options=q_data['options'],
                correct_answer=q_data['correct_answer'],
                explanation=q_data['explanation'],
                points=q_data.get('points', 10),
                estimated_time_seconds=q_data.get('estimated_time_seconds', 60),
                is_verified=False  # Needs admin review
            )
            created_count += 1
        
        logger.info(f"Created {created_count} questions for test {test.title}")
        return created_count
    
    def generate_code_challenges(self, skill_name, difficulty, count=5):
        """Generate coding challenge questions."""
        return self.generate_questions(
            skill_name=skill_name,
            difficulty=difficulty,
            count=count,
            question_type='CODE'
        )

    def generate_adaptive_questions(self, user_score, skill_name, count=10):
        """Adjust difficulty based on previous performance."""
        if user_score >= 80:
            difficulty = 'ADVANCED'
        elif user_score >= 60:
            difficulty = 'INTERMEDIATE'
        else:
            difficulty = 'BEGINNER'
        return self.generate_questions(skill_name, difficulty, count)


def generate_questions_for_skill(skill_name, difficulty='INTERMEDIATE', count=20):
    """
    Convenience function to generate questions for a skill
    Can be called from Django shell or management commands
    """
    try:
        generator = QuestionGenerator()
    except (ValueError, ImportError) as exc:
        logger.error(f"Question generation skipped: {exc}")
        return []
    questions = generator.generate_questions(skill_name, difficulty, count)
    
    from .models import QuestionPool
    
    created = []
    for q_data in questions:
        question = QuestionPool.objects.create(
            skill_name=skill_name,
            difficulty=difficulty,
            question_type='MULTIPLE_CHOICE',
            question=q_data['question'],
            options=q_data['options'],
            correct_answer=q_data['correct_answer'],
            explanation=q_data['explanation'],
            points=q_data.get('points', 10),
            estimated_time_seconds=q_data.get('estimated_time_seconds', 60),
            is_verified=False
        )
        created.append(question)
        
    return created

# Signal handlers to auto-track events
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import QuestionPool

@receiver(post_save, sender=QuestionPool)
def on_question_created(sender, instance, created, **kwargs):
    """Auto-log when a new question is created"""
    if created:
        logger.info(f"New question created: {instance.id} for skill {instance.skill_name}")
        
        # Additional tracking logic can be added here
        # e.g., updating analytics, notifying admins, etc.
        


        
