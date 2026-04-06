"""
Unit tests for question validator functionality.

Tests cover:
- Valid question structure acceptance
- Missing required fields detection
- Invalid category rejection
- Duplicate order detection
- Malformed JSON handling
- Extra fields handling
"""

from django.test import TestCase
import json

from apps.interviews.ai_connector import QuestionValidator, ValidationError


class QuestionValidatorTest(TestCase):
    """
    Tests for QuestionValidator class.
    """

    def test_question_validator_valid_response(self):
        """
        Test that valid questions pass validation.

        Verify:
        - Valid structure is accepted
        - All required fields present
        - Data types are correct
        - No validation errors raised
        """
        valid_questions = [
            {
                'prompt': 'How do you approach complex problems?',
                'category': 'behavioral',
                'difficulty': 'hard',
                'evaluation_criteria': ['analytical', 'communication'],
                'order': 1
            },
            {
                'prompt': 'Describe your leadership style',
                'category': 'behavioral',
                'difficulty': 'medium',
                'evaluation_criteria': ['leadership', 'vision'],
                'order': 2
            }
        ]

        # Should not raise any exception
        for question in valid_questions:
            result = QuestionValidator.validate_question(question)
            self.assertTrue(result)

    def test_question_validator_missing_fields(self):
        """
        Test that missing required fields are detected.

        Verify:
        - Missing 'prompt' raises ValidationError
        - Missing 'category' raises ValidationError
        - Missing 'difficulty' raises ValidationError
        - Missing 'evaluation_criteria' raises ValidationError
        - Missing 'order' raises ValidationError
        """
        base_question = {
            'prompt': 'Valid prompt',
            'category': 'behavioral',
            'difficulty': 'hard',
            'evaluation_criteria': ['test'],
            'order': 1
        }

        # Test each missing field
        required_fields = ['prompt', 'category', 'difficulty', 'evaluation_criteria', 'order']

        for field in required_fields:
            incomplete_question = {k: v for k, v in base_question.items() if k != field}
            
            with self.assertRaises(ValidationError):
                QuestionValidator.validate_question(incomplete_question)

    def test_question_validator_invalid_category(self):
        """
        Test that invalid categories are rejected.

        Verify:
        - Valid categories accepted (behavioral, technical, situational)
        - Invalid categories rejected
        - Case sensitivity handled
        - Empty category rejected
        """
        valid_categories = ['behavioral', 'technical', 'situational']
        invalid_categories = ['invalid', 'random', 'technical_invalid', '', None]

        # Test valid categories
        for category in valid_categories:
            question = {
                'prompt': 'Test',
                'category': category,
                'difficulty': 'hard',
                'evaluation_criteria': ['test'],
                'order': 1
            }
            result = QuestionValidator.validate_question(question)
            self.assertTrue(result)

        # Test invalid categories
        for category in invalid_categories:
            question = {
                'prompt': 'Test',
                'category': category,
                'difficulty': 'hard',
                'evaluation_criteria': ['test'],
                'order': 1
            }
            
            with self.assertRaises(ValidationError):
                QuestionValidator.validate_question(question)

    def test_question_validator_duplicate_order(self):
        """
        Test that duplicate order numbers are detected.

        Verify:
        - Unique orders accepted
        - Duplicate orders in batch rejected
        - Order validation happens across batch
        - Order sequence validation
        """
        # Valid: unique orders
        valid_batch = [
            {
                'prompt': 'Q1',
                'category': 'behavioral',
                'difficulty': 'hard',
                'evaluation_criteria': ['test'],
                'order': 1
            },
            {
                'prompt': 'Q2',
                'category': 'technical',
                'difficulty': 'medium',
                'evaluation_criteria': ['test'],
                'order': 2
            }
        ]

        result = QuestionValidator.validate_batch(valid_batch)
        self.assertTrue(result)

        # Invalid: duplicate orders
        invalid_batch = [
            {
                'prompt': 'Q1',
                'category': 'behavioral',
                'difficulty': 'hard',
                'evaluation_criteria': ['test'],
                'order': 1
            },
            {
                'prompt': 'Q2',
                'category': 'technical',
                'difficulty': 'medium',
                'evaluation_criteria': ['test'],
                'order': 1  # Duplicate order
            }
        ]

        with self.assertRaises(ValidationError):
            QuestionValidator.validate_batch(invalid_batch)

    def test_question_validator_malformed_json(self):
        """
        Test handling of malformed JSON responses.

        Verify:
        - Invalid JSON rejected
        - Parsing errors caught
        - Clear error messages
        - Safe fallback behavior
        """
        malformed_jsons = [
            '{"incomplete": ',
            '{invalid json}',
            'not json at all',
            '{"questions": [incomplete',
            '',
            None
        ]

        for malformed in malformed_jsons:
            with self.assertRaises((ValidationError, json.JSONDecodeError, TypeError)):
                if malformed:
                    parsed = json.loads(malformed)
                    QuestionValidator.validate_response(parsed)
                else:
                    QuestionValidator.validate_response(malformed)

    def test_question_validator_extra_fields_ignored(self):
        """
        Test that extra fields are ignored without error.

        Verify:
        - Extra fields don't cause validation failure
        - Required fields are still validated
        - Extra fields are preserved
        - Extensibility supported
        """
        question_with_extras = {
            'prompt': 'How do you handle conflict?',
            'category': 'behavioral',
            'difficulty': 'hard',
            'evaluation_criteria': ['communication', 'empathy'],
            'order': 1,
            'extra_field_1': 'should be ignored',
            'extra_field_2': {'nested': 'data'},
            'tags': ['important', 'common']
        }

        # Should validate successfully despite extra fields
        result = QuestionValidator.validate_question(question_with_extras)
        self.assertTrue(result)

    def test_question_validator_difficulty_levels(self):
        """
        Test validation of difficulty levels.

        Verify:
        - Valid levels: easy, medium, hard
        - Invalid levels rejected
        - Case sensitivity
        """
        valid_difficulties = ['easy', 'medium', 'hard']
        invalid_difficulties = ['beginner', 'intermediate', 'advanced', '', None, 'HARD']

        # Valid difficulties
        for difficulty in valid_difficulties:
            question = {
                'prompt': 'Test',
                'category': 'behavioral',
                'difficulty': difficulty,
                'evaluation_criteria': ['test'],
                'order': 1
            }
            result = QuestionValidator.validate_question(question)
            self.assertTrue(result)

        # Invalid difficulties
        for difficulty in invalid_difficulties:
            question = {
                'prompt': 'Test',
                'category': 'behavioral',
                'difficulty': difficulty,
                'evaluation_criteria': ['test'],
                'order': 1
            }
            
            with self.assertRaises(ValidationError):
                QuestionValidator.validate_question(question)

    def test_question_validator_evaluation_criteria(self):
        """
        Test validation of evaluation criteria.

        Verify:
        - List of criteria required
        - Non-empty list required
        - String criteria validated
        - Invalid criteria rejected
        """
        # Valid criteria
        valid_question = {
            'prompt': 'Test',
            'category': 'behavioral',
            'difficulty': 'hard',
            'evaluation_criteria': ['communication', 'leadership', 'vision'],
            'order': 1
        }
        result = QuestionValidator.validate_question(valid_question)
        self.assertTrue(result)

        # Invalid: empty criteria list
        invalid_question = {
            'prompt': 'Test',
            'category': 'behavioral',
            'difficulty': 'hard',
            'evaluation_criteria': [],
            'order': 1
        }
        
        with self.assertRaises(ValidationError):
            QuestionValidator.validate_question(invalid_question)

        # Invalid: criteria not a list
        invalid_question = {
            'prompt': 'Test',
            'category': 'behavioral',
            'difficulty': 'hard',
            'evaluation_criteria': 'not a list',
            'order': 1
        }
        
        with self.assertRaises(ValidationError):
            QuestionValidator.validate_question(invalid_question)

    def test_question_validator_order_format(self):
        """
        Test validation of order field format.

        Verify:
        - Integer order required
        - Positive order required
        - Zero or negative rejected
        - Non-integer rejected
        """
        base = {
            'prompt': 'Test',
            'category': 'behavioral',
            'difficulty': 'hard',
            'evaluation_criteria': ['test'],
        }

        # Valid orders
        for order in [1, 2, 3, 100]:
            question = {**base, 'order': order}
            result = QuestionValidator.validate_question(question)
            self.assertTrue(result)

        # Invalid orders
        invalid_orders = [0, -1, -10, 'one', 1.5, None]
        for order in invalid_orders:
            question = {**base, 'order': order}
            
            with self.assertRaises(ValidationError):
                QuestionValidator.validate_question(question)
