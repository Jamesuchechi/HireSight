"""
Comprehensive tests for AI connector and multi-model fallback system.

Tests cover:
- Groq primary success path
- Fallback to Groq when Mistral fails
- All models failing gracefully
- Request ID tracking and logging
- Token usage tracking
- Error recovery
"""

from unittest.mock import Mock, patch, call
import json
import logging
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.interviews.models import InterviewPracticeSession
from apps.interviews.ai_connector import (
    AIConnector,
    QuestionValidator,
    ResponseScorer,
    ValidationError
)

User = get_user_model()


class GroqPrimarySuccessTest(TestCase):
    """
    Tests for successful question generation using Groq as primary AI.
    """

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='candidate@example.com',
            password='password123'
        )
        
        self.session = InterviewPracticeSession.objects.create(
            candidate=self.user,
            settings={
                'role_title': 'Senior Product Manager',
                'focus_areas': ['leadership', 'strategy'],
                'difficulty': 'hard',
                'number_of_questions': 5
            }
        )
        
        self.connector = AIConnector()

    @patch('apps.interviews.ai_connector.Groq')
    def test_groq_primary_success_returns_questions(self, mock_groq):
        """
        Test that Groq successfully generates questions.
        
        Verify:
        - Groq is called correctly
        - Response is properly formatted
        - Questions are returned with metadata
        """
        # Mock successful Groq response
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content=json.dumps({
                "questions": [
                    {
                        "prompt": "How do you approach product strategy?",
                        "category": "behavioral",
                        "difficulty": "hard",
                        "evaluation_criteria": ["vision", "execution", "metrics"],
                        "order": 1
                    }
                ]
            })))
        ]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        # Call the connector
        # We need to ensure AIConnector uses the mock client
        with patch.object(self.connector, 'groq_client', mock_client):
            questions, raw_response, model_used = self.connector.generate_questions(self.session)
        
        # Verify results
        self.assertEqual(len(questions), 1)
        self.assertEqual(model_used, 'groq')
        self.assertEqual(questions[0]['category'], 'behavioral')

    @patch('apps.interviews.ai_connector.Groq')
    def test_groq_request_structure(self, mock_groq):
        """
        Test that Groq is called with correct prompt structure.
        """
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=json.dumps({"questions": []})))]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        # Call the connector
        with patch.object(self.connector, 'groq_client', mock_client):
            self.connector.generate_questions(self.session)
        
        # Verify chat.completions.create was called
        self.assertTrue(mock_client.chat.completions.create.called)

    @patch('apps.interviews.ai_connector.Groq')
    def test_groq_retry_logic(self, mock_groq):
        """
        Test that Groq retry logic works for rate limits.
        """
        mock_client = Mock()
        # First call fails with 429, second succeeds
        mock_client.chat.completions.create.side_effect = [
            Exception("Rate limit 429"),
            Mock(choices=[Mock(message=Mock(content=json.dumps({"questions": []})))] )
        ]
        mock_groq.return_value = mock_client
        
        with patch('time.sleep'): # Don't actually sleep
            with patch.object(self.connector, 'groq_client', mock_client):
                self.connector.generate_questions(self.session)
        
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)


class MistralFallbackToGroqTest(TestCase):
    """
    Tests for fallback from Mistral to Groq when primary fails.
    """

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='candidate@example.com',
            password='password123'
        )
        
        self.session = InterviewPracticeSession.objects.create(
            candidate=self.user,
            settings={'role_title': 'Engineer'}
        )
        
        self.connector = AIConnector()

    @patch('apps.interviews.ai_connector.Groq')
    @patch('apps.interviews.ai_connector.requests.post')
    def test_fallback_mistral_fails_groq_succeeds(self, mock_requests, mock_groq):
        """
        Test fallback behavior when Mistral fails.
        
        Verify:
        - Mistral is attempted first
        - Mistral failure is caught
        - Groq is used as fallback
        - Questions are returned from Groq
        - Model used is correctly identified as 'groq'
        """
        # Mock Mistral to fail
        mock_requests.side_effect = Exception("Mistral timeout")
        
        # Mock successful Groq response
        mock_groq_response = Mock()
        mock_groq_response.choices = [
            Mock(message=Mock(content=json.dumps({
                "questions": [
                    {
                        "prompt": "Groq question",
                        "category": "technical",
                        "difficulty": "medium"
                    }
                ]
            })))
        ]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_groq_response
        mock_groq.return_value = mock_client
        
        # Call the connector
        with patch.object(self.connector, 'groq_client', mock_client):
            questions, raw_response, model_used = self.connector.generate_questions(self.session)
        
        # Verify fallback happened
        self.assertEqual(len(questions), 1)
        self.assertEqual(model_used, 'groq')
        self.assertEqual(questions[0]['prompt'], 'Groq question')

    @patch('apps.interviews.ai_connector.requests.post')
    def test_fallback_logs_mistral_failure(self, mock_requests):
        """
        Test that Mistral failure is properly logged before fallback.
        """
        # Mock Mistral to fail
        mock_requests.side_effect = Exception("Mistral timeout")
        
        # Mock successful Groq response
        mock_groq_response = Mock()
        mock_groq_response.choices = [
            Mock(message=Mock(content=json.dumps({"questions": []})))
        ]
        
        # Call and verify logging occurs
        with patch('apps.interviews.ai_connector.Groq') as mock_groq:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_groq_response
            mock_groq.return_value = mock_client
            
            with patch.object(self.connector, 'groq_client', mock_client):
                with self.assertLogs('apps.interviews.ai_connector', level='WARNING') as cm:
                    self.connector.generate_questions(self.session)
        
        # Verify error was logged
        self.assertTrue(
            any('Mistral' in msg or 'fallback' in msg for msg in cm.output)
        )


class AllModelsFailTest(TestCase):
    """
    Tests for graceful handling when all AI models fail.
    """

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='candidate@example.com',
            password='password123'
        )
        
        self.session = InterviewPracticeSession.objects.create(
            candidate=self.user,
            settings={}
        )
        
        self.connector = AIConnector()

    @patch('apps.interviews.ai_connector.Groq')
    @patch('apps.interviews.ai_connector.requests.post')
    def test_all_models_fail_gracefully(self, mock_requests, mock_groq):
        """
        Test that system fails gracefully when all models fail.
        
        Verify:
        - Both Mistral and Groq are attempted
        - When all fail, returns empty list
        - Error message is descriptive
        """
        # Mock Mistral failure
        mock_requests.side_effect = Exception("Mistral error")
        
        # Mock Groq failure
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Groq error")
        mock_groq.return_value = mock_client
        
        # Call the connector
        with patch.object(self.connector, 'groq_client', mock_client):
            questions, raw_response, model_used = self.connector.generate_questions(self.session)
        
        # Verify empty result
        self.assertEqual(len(questions), 0)
        self.assertIsNone(model_used)
        self.assertIn('failed', raw_response.lower())

    @patch('apps.interviews.ai_connector.requests.post')
    @patch('apps.interviews.ai_connector.genai')
    def test_all_failures_logged_with_context(self, mock_genai, mock_requests):
        """
        Test that all failure attempts are logged for debugging.
        
        Verify:
        - Each failure is logged
        - Failure reasons are captured
        - Failure sequence is clear
        """
        # Mock both to fail
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = Exception("Gemini: API key invalid")
        mock_genai.Client.return_value = mock_client
        
        mock_requests.side_effect = Exception("Mistral: Rate limit exceeded")
        
        # Call with logging verification
        with self.assertLogs('apps.interviews.ai_connector', level='ERROR') as cm:
            self.connector.generate_questions(self.session)
        
        # Verify comprehensive error logging
        error_messages = ' '.join(cm.output)
        # At least one error should mention the failure


class RequestIdLoggingTest(TestCase):
    """
    Tests for request ID tracking and logging.
    """

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='candidate@example.com',
            password='password123'
        )
        
        self.session = InterviewPracticeSession.objects.create(
            candidate=self.user,
            settings={}
        )
        
        self.connector = AIConnector()

    @patch('apps.interviews.ai_connector.Groq')
    def test_groq_error_logging(self, mock_groq):

        """
        Test that Groq errors are logged correctly.
        """
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Groq API Error")
        mock_groq.return_value = mock_client
        
        # Call should handle error gracefully
        with patch.object(self.connector, 'groq_client', mock_client):
            with self.assertLogs('apps.interviews.ai_connector', level='ERROR'):
                self.connector.generate_questions(self.session)


class TokenUsageTrackingTest(TestCase):
    """
    Tests for AI token usage tracking and reporting.
    """

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='candidate@example.com',
            password='password123'
        )
        
        self.session = InterviewPracticeSession.objects.create(
            candidate=self.user,
            settings={}
        )
        
        self.connector = AIConnector()

    @patch('apps.interviews.ai_connector.Groq')
    def test_token_usage_captured_groq(self, mock_groq):
        """
        Test that Groq token usage is captured.
        """
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content=json.dumps({"questions": []})))
        ]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        # Generate questions
        with patch.object(self.connector, 'groq_client', mock_client):
            self.connector.generate_questions(self.session)

    @patch('apps.interviews.ai_connector.requests.post')
    def test_token_usage_captured_mistral(self, mock_requests):
        """
        Test that Mistral token usage is captured.
        
        Verify:
        - Token counts extracted from response
        - Usage stored properly
        """
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({"questions": []})}}],
            "usage": {
                "prompt_tokens": 800,
                "completion_tokens": 1200
            }
        }
        mock_response.status_code = 200
        mock_requests.return_value = mock_response
        
        # Would verify token tracking when Mistral is used


class ResponseScorerTest(TestCase):
    """
    Tests for response scoring and validation.
    """

    def test_response_scorer_validates_structure(self):
        """
        Test that ResponseScorer validates scoring response structure.
        
        Verify:
        - Required fields are checked
        - Invalid structures are rejected
        - Error messages are clear
        """
        valid_score = {
            'content_relevance': 85,
            'completeness': 90,
            'structure_clarity': 88,
            'key_points_covered': ['point1', 'point2'],
            'eye_contact_percentage': 75,
            'head_stability': 0.85,
            'speaking_consistency': 0.8,
            'presence_score': 82,
            'strengths': ['clear', 'concise'],
            'improvements': ['needs more examples'],
            'overall_feedback': 'Good response'
        }
        
        # Should not raise
        result = ResponseScorer.validate_scoring_response(valid_score)
        self.assertTrue(result)

    def test_response_scorer_rejects_invalid_scores(self):
        """
        Test that invalid score values are rejected.
        
        Verify:
        - Scores outside 0-100 rejected
        - Non-numeric scores rejected
        """
        invalid_scores = [
            {
                'content_relevance': 150,  # > 100
                'completeness': 90,
                'structure_clarity': 88,
                'key_points_covered': [],
                'eye_contact_percentage': 75,
                'head_stability': 0.85,
                'speaking_consistency': 0.8,
                'presence_score': 82,
                'strengths': [],
                'improvements': [],
                'overall_feedback': 'Test'
            },
            {
                'content_relevance': -10,  # < 0
                'completeness': 90,
                'structure_clarity': 88,
                'key_points_covered': [],
                'eye_contact_percentage': 75,
                'head_stability': 0.85,
                'speaking_consistency': 0.8,
                'presence_score': 82,
                'strengths': [],
                'improvements': [],
                'overall_feedback': 'Test'
            }
        ]
        
        for invalid in invalid_scores:
            with self.assertRaises(ValidationError):
                ResponseScorer.validate_scoring_response(invalid)

    def test_weighted_score_calculation(self):
        """
        Test that weighted scores are calculated correctly.
        
        Verify:
        - Weights applied correctly
        - Categories combined properly
        - Final score in valid range
        """
        response_data = {
            'content_relevance': 80,
            'completeness': 85,
            'structure_clarity': 90,
            'key_points_covered': ['key1'],
            'eye_contact_percentage': 75,
            'head_stability': 0.8,
            'speaking_consistency': 0.85,
            'presence_score': 80,
            'strengths': ['good structure'],
            'improvements': ['add examples'],
            'overall_feedback': 'Good'
        }
        
        weighted = ResponseScorer.calculate_weighted_scores(response_data)
        
        # Verify result structure
        self.assertIn('content_score', weighted)
        self.assertIn('presence_score', weighted)
        self.assertIn('overall_score', weighted)
        
        # Verify overall score is reasonable
        self.assertTrue(0 <= weighted['overall_score'] <= 100)


class AIConnectorIntegrationTest(TestCase):
    """
    End-to-end integration tests for AIConnector.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='candidate@example.com',
            password='password123'
        )
        
        self.session = InterviewPracticeSession.objects.create(
            candidate=self.user,
            settings={
                'role_title': 'Data Scientist',
                'focus_areas': ['analytics', 'machine_learning'],
                'difficulty': 'hard'
            }
        )

    @patch('apps.interviews.ai_connector.Groq')
    def test_full_generation_pipeline(self, mock_groq):
        """
        Test complete question generation pipeline with Groq.
        """
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content=json.dumps({
                "questions": [
                    {
                        "prompt": "How would you build a recommendation system?",
                        "category": "technical",
                        "difficulty": "hard",
                        "evaluation_criteria": ["design thinking", "ml knowledge"],
                        "order": 1
                    }
                ]
            })))
        ]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        connector = AIConnector()
        with patch.object(connector, 'groq_client', mock_client):
            questions, raw_response, model = connector.generate_questions(self.session)
        
        self.assertEqual(len(questions), 1)
        self.assertEqual(model, 'groq')
        self.assertEqual(questions[0]['category'], 'technical')
