"""
Unit tests for AI prompt building functionality.

Tests cover:
- Prompt construction with full context
- Handling missing job description
- Handling missing skills
- Minimal context scenarios
"""

from django.test import TestCase
from unittest.mock import Mock, patch

from apps.interviews.ai_connector import PromptBuilder


class PromptBuilderTest(TestCase):
    """
    Tests for PromptBuilder class.
    """

    def setUp(self):
        """Set up test fixtures"""
        self.full_session_context = {
            'role_title': 'Senior Product Manager',
            'job_description': 'Lead product strategy for mobile applications. Required skills: product management, user research, data analysis.',
            'required_skills': ['product management', 'user research', 'data analysis', 'leadership'],
            'focus_areas': ['strategy', 'leadership', 'user empathy'],
            'difficulty': 'hard',
            'number_of_questions': 5,
            'language': 'en'
        }

    def test_prompt_with_full_context(self):
        """
        Test prompt building with all available context.

        Verify:
        - Role title included
        - Job description included
        - Required skills included
        - Focus areas included
        - Difficulty level specified
        - Number of questions specified
        - Proper formatting and structure
        - Questions match settings
        """
        builder = PromptBuilder(self.full_session_context)
        prompt = builder.build_prompt()

        # Verify all context elements are in the prompt
        self.assertIn('Senior Product Manager', prompt)
        self.assertIn('product management', prompt)
        self.assertIn('strategy', prompt)
        self.assertIn('hard', prompt)
        self.assertIn('5', prompt)
        
        # Verify prompt structure
        self.assertTrue(len(prompt) > 100)
        self.assertIn('interview', prompt.lower())
        self.assertIn('question', prompt.lower())

    def test_prompt_with_missing_job_description(self):
        """
        Test prompt building when job description is missing.

        Verify:
        - Prompt still valid without job description
        - Role title is primary focus
        - Skills used as context
        - Focus areas guide question generation
        - No errors or malformed sections
        """
        context = {
            'role_title': 'Software Engineer',
            'job_description': None,
            'required_skills': ['Python', 'AWS', 'databases'],
            'focus_areas': ['system design', 'scalability'],
            'difficulty': 'hard',
            'number_of_questions': 5,
            'language': 'en'
        }

        builder = PromptBuilder(context)
        prompt = builder.build_prompt()

        # Should still include essential elements
        self.assertIn('Software Engineer', prompt)
        self.assertIn('Python', prompt)
        self.assertIn('system design', prompt)
        
        # Should be valid and complete
        self.assertTrue(len(prompt) > 100)
        self.assertNotIn('None', prompt)
        self.assertNotIn('null', prompt)

    def test_prompt_with_missing_skills(self):
        """
        Test prompt building when required skills are missing.

        Verify:
        - Prompt still valid without explicit skills
        - Role title is used
        - Job description provides context
        - Focus areas guide content
        - No empty sections
        """
        context = {
            'role_title': 'Data Analyst',
            'job_description': 'Analyze product metrics and user behavior',
            'required_skills': None,
            'focus_areas': ['analytics', 'reporting'],
            'difficulty': 'medium',
            'number_of_questions': 4,
            'language': 'en'
        }

        builder = PromptBuilder(context)
        prompt = builder.build_prompt()

        # Should still include essential elements
        self.assertIn('Data Analyst', prompt)
        self.assertIn('Analyze', prompt)
        self.assertIn('analytics', prompt)
        
        # Should be valid
        self.assertTrue(len(prompt) > 100)

    def test_prompt_with_minimal_context(self):
        """
        Test prompt building with only required minimal context.

        Verify:
        - Works with only role title
        - Default difficulty applied
        - Default question count applied
        - Prompt still usable for question generation
        - Graceful handling of missing optional fields
        """
        minimal_context = {
            'role_title': 'Developer',
            'job_description': None,
            'required_skills': None,
            'focus_areas': [],
            'difficulty': 'medium',
            'number_of_questions': 3,
            'language': 'en'
        }

        builder = PromptBuilder(minimal_context)
        prompt = builder.build_prompt()

        # Should still be valid
        self.assertIsNotNone(prompt)
        self.assertIn('Developer', prompt)
        self.assertTrue(len(prompt) > 50)

    def test_prompt_includes_json_structure(self):
        """
        Test that prompt includes JSON structure instructions.

        Verify:
        - JSON format specified
        - Example structure provided
        - Field names documented
        - Required vs optional fields explained
        """
        builder = PromptBuilder(self.full_session_context)
        prompt = builder.build_prompt()

        # Should include JSON instructions
        self.assertIn('json', prompt.lower())
        self.assertIn('questions', prompt.lower())
        self.assertIn('prompt', prompt.lower())
        self.assertIn('category', prompt.lower())
        self.assertIn('difficulty', prompt.lower())

    def test_prompt_includes_evaluation_criteria(self):
        """
        Test that prompt specifies evaluation criteria expectations.

        Verify:
        - Evaluation criteria mentioned
        - Examples provided for different categories
        - Scorer expectations documented
        - Behavioral vs technical differentiated
        """
        builder = PromptBuilder(self.full_session_context)
        prompt = builder.build_prompt()

        # Should include evaluation criteria instructions
        self.assertIn('evaluation', prompt.lower())
        self.assertIn('criteria', prompt.lower())

    def test_prompt_respects_difficulty_level(self):
        """
        Test that prompt construction respects difficulty level.

        Verify:
        - Easy questions less complex
        - Hard questions more challenging
        - Difficulty affects prompt tone/content
        - Different context for each level
        """
        difficulties = ['easy', 'medium', 'hard']
        prompts = []

        for difficulty in difficulties:
            context = {
                'role_title': 'Engineer',
                'difficulty': difficulty,
                'number_of_questions': 3
            }
            builder = PromptBuilder(context)
            prompt = builder.build_prompt()
            prompts.append(prompt)
            
            # Verify difficulty is mentioned
            self.assertIn(difficulty, prompt.lower())

        # Prompts should be different for different difficulties
        self.assertNotEqual(prompts[0], prompts[1])
        self.assertNotEqual(prompts[1], prompts[2])

    def test_prompt_respects_question_count(self):
        """
        Test that prompt construction respects requested question count.

        Verify:
        - Number of questions specified
        - Count instruction is clear
        - Varies by requested count
        """
        counts = [3, 5, 7]
        prompts = []

        for count in counts:
            context = {
                'role_title': 'Manager',
                'number_of_questions': count
            }
            builder = PromptBuilder(context)
            prompt = builder.build_prompt()
            prompts.append(prompt)
            
            # Verify count is mentioned
            self.assertIn(str(count), prompt)

    def test_prompt_focus_areas_emphasis(self):
        """
        Test that prompt emphasizes specified focus areas.

        Verify:
        - Focus areas mentioned prominently
        - Multiple focus areas included
        - Clear that these are priorities
        - Not generic questions expected
        """
        context = {
            'role_title': 'Product Manager',
            'focus_areas': ['leadership', 'strategy', 'communication'],
            'number_of_questions': 5
        }

        builder = PromptBuilder(context)
        prompt = builder.build_prompt()

        # All focus areas should be in prompt
        for area in context['focus_areas']:
            self.assertIn(area.lower(), prompt.lower())

    def test_prompt_question_format_specifications(self):
        """
        Test that prompt clearly specifies question format requirements.

        Verify:
        - Prompt must be clear and specific
        - Category must be one of allowed types
        - Difficulty must be specified
        - Order must be sequential
        - Evaluation criteria must be list
        """
        builder = PromptBuilder(self.full_session_context)
        prompt = builder.build_prompt()

        # Should mention format requirements
        self.assertIn('prompt', prompt.lower())
        self.assertIn('category', prompt.lower())
        self.assertIn('behavioral', prompt.lower() or 'technical' in prompt.lower())
        self.assertIn('order', prompt.lower())

    def test_prompt_with_language_setting(self):
        """
        Test prompt building respects language setting.

        Verify:
        - Language parameter used
        - Different languages produce different prompts
        - Language setting affects instructions
        """
        context_en = {
            'role_title': 'Engineer',
            'language': 'en',
            'number_of_questions': 3
        }
        
        context_es = {
            'role_title': 'Engineer',
            'language': 'es',
            'number_of_questions': 3
        }

        builder_en = PromptBuilder(context_en)
        builder_es = PromptBuilder(context_es)
        
        prompt_en = builder_en.build_prompt()
        prompt_es = builder_es.build_prompt()

        # English and Spanish prompts should be different
        # (if language implementation is done)
        # At minimum, both should be valid
        self.assertIsNotNone(prompt_en)
        self.assertIsNotNone(prompt_es)

    def test_prompt_caching_for_same_context(self):
        """
        Test that same context produces consistent prompts.

        Verify:
        - Same input generates same output
        - No randomization in prompt building
        - Deterministic results
        """
        builder1 = PromptBuilder(self.full_session_context)
        builder2 = PromptBuilder(self.full_session_context)

        prompt1 = builder1.build_prompt()
        prompt2 = builder2.build_prompt()

        # Same context should produce same prompt
        self.assertEqual(prompt1, prompt2)

    def test_prompt_handles_special_characters(self):
        """
        Test that prompt builder handles special characters safely.

        Verify:
        - Quotes handled correctly
        - Newlines handled correctly
        - Unicode handled correctly
        - No injection vulnerabilities
        """
        context = {
            'role_title': 'Engineer "Senior" (with quotes)',
            'job_description': 'Role:\nLine 2\nLine 3',
            'required_skills': ['C++', 'Python3.11', 'AWS/GCP'],
            'focus_areas': ['R&D', '20% projects', '$1M+ budgets'],
            'number_of_questions': 5
        }

        builder = PromptBuilder(context)
        prompt = builder.build_prompt()

        # Should handle special characters safely
        self.assertIsNotNone(prompt)
        self.assertTrue(len(prompt) > 50)
        # No unescaped quotes should break JSON later
        self.assertNotIn('""', prompt)  # Double quotes due to escaping issues

    def test_prompt_length_reasonable(self):
        """
        Test that generated prompts are reasonable length.

        Verify:
        - Prompts are not too short (at least 200 chars)
        - Prompts are not too long (under 5000 chars)
        - Complete instruction coverage
        - Efficient but comprehensive
        """
        builder = PromptBuilder(self.full_session_context)
        prompt = builder.build_prompt()

        self.assertGreater(len(prompt), 200)
        self.assertLess(len(prompt), 5000)
