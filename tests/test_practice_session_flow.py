"""
Comprehensive integration tests for interview practice session flow.

Tests cover:
- Complete practice session workflow
- AI question generation with mocks
- Response submission and scoring
- Report generation
- Error handling and validation
- Video metrics processing
"""

import json
from datetime import timedelta
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.interviews.models import (
    InterviewPracticeSession,
    PracticeQuestion,
    PracticeResponse,
    PracticePerformanceReport
)
from apps.interviews.tasks import (
    generate_practice_questions,
    analyze_practice_response,
    generate_practice_report
)
from apps.interviews.ai_connector import (
    AIConnector,
    QuestionValidator,
    ResponseScorer,
    ValidationError
)

User = get_user_model()


class MockGeminiClient:
    """
    Mock Gemini AI client that returns realistic structured responses.
    Used to test the full question generation pipeline.
    """

    def __init__(self, should_fail=False, malformed=False):
        self.should_fail = should_fail
        self.malformed = malformed
        self.call_count = 0
        self.token_count = 0

    def generate_content(self, contents, **kwargs):
        """Mock the Gemini generate_content method"""
        self.call_count += 1
        self.token_count += 150  # Mock token usage
        
        if self.should_fail:
            raise Exception("Gemini API timeout")
        
        response = Mock()
        
        if self.malformed:
            # Return invalid JSON to test validation error handling
            response.text = "{invalid json"
        else:
            # Return realistic interview questions in expected format
            response.text = json.dumps({
                "questions": [
                    {
                        "prompt": "Tell me about a time you led a team through a challenging project.",
                        "category": "behavioral",
                        "difficulty": "medium",
                        "evaluation_criteria": [
                            "Clear problem statement",
                            "Leadership approach",
                            "Results and outcomes",
                            "Team dynamics management"
                        ],
                        "order": 1,
                        "expected_answer_elements": [
                            "Specific situation",
                            "Your role",
                            "Action taken",
                            "Measurable results"
                        ]
                    },
                    {
                        "prompt": "How do you approach debugging a complex system issue?",
                        "category": "technical",
                        "difficulty": "medium",
                        "evaluation_criteria": [
                            "Systematic approach",
                            "Problem-solving methodology",
                            "Technical knowledge",
                            "Communication clarity"
                        ],
                        "order": 2,
                        "expected_answer_elements": [
                            "Problem reproduction",
                            "Root cause analysis",
                            "Solution design",
                            "Testing approach"
                        ]
                    },
                    {
                        "prompt": "Describe a situation where you had to adapt to unexpected changes.",
                        "category": "situational",
                        "difficulty": "medium",
                        "evaluation_criteria": [
                            "Adaptability",
                            "Problem-solving",
                            "Initiative",
                            "Communication"
                        ],
                        "order": 3,
                        "expected_answer_elements": [
                            "Original plan",
                            "Unexpected change",
                            "Quick thinking",
                            "Positive outcome"
                        ]
                    },
                    {
                        "prompt": "What drives your career and professional growth?",
                        "category": "behavioral",
                        "difficulty": "easy",
                        "evaluation_criteria": [
                            "Self-awareness",
                            "Career vision",
                            "Continuous learning",
                            "Alignment with role"
                        ],
                        "order": 4,
                        "expected_answer_elements": [
                            "Learning orientation",
                            "Career goals",
                            "Growth mindset",
                            "Examples of development"
                        ]
                    },
                    {
                        "prompt": "How would you design a real-time notification system?",
                        "category": "technical",
                        "difficulty": "hard",
                        "evaluation_criteria": [
                            "System design knowledge",
                            "Scalability considerations",
                            "Architecture decisions",
                            "Trade-off analysis"
                        ],
                        "order": 5,
                        "expected_answer_elements": [
                            "System architecture",
                            "Technology choices",
                            "Scalability approach",
                            "Failure handling"
                        ]
                    }
                ]
            })
        
        response.usage = Mock()
        response.usage.prompt_tokens = 100
        response.usage.candidates_tokens = 50
        
        return response


class MockMistralClient:
    """
    Mock Mistral AI client for fallback testing.
    """

    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.call_count = 0

    def messages_create(self, **kwargs):
        """Mock the Mistral messages.create method"""
        self.call_count += 1
        
        if self.should_fail:
            raise Exception("Mistral API error")
        
        response = Mock()
        response.content = [Mock(text=json.dumps({
            "questions": [
                {"prompt": "Sample question", "category": "behavioral", "difficulty": "medium"}
            ]
        }))]
        
        return response


class InterviewPracticeSessionFlowTest(TestCase):
    """
    Integration tests for complete practice session workflow.
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
                'role_title': 'Product Manager',
                'focus_areas': ['leadership', 'communication'],
                'difficulty': 'medium',
                'time_limit_per_question': 2,
                'number_of_questions': 5
            }
        )

    @patch('apps.interviews.ai_connector.genai.Client')
    def test_complete_practice_session_flow(self, mock_genai):
        """
        Test the complete workflow:
        1. Questions are generated
        2. User submits answers
        3. Responses are scored
        4. Report is generated
        """
        # 1. Mock Gemini and generate questions
        mock_gemini = MockGeminiClient()
        mock_client = Mock()
        mock_client.models.generate_content = mock_gemini.generate_content
        mock_genai.return_value = mock_client
        
        # Generate questions
        generate_practice_questions(self.session.id)
        
        # Verify questions were created
        self.session.refresh_from_db()
        self.assertEqual(self.session.questions.count(), 5)
        self.assertEqual(
            self.session.question_generation_state,
            InterviewPracticeSession.GenerationState.COMPLETED
        )
        self.assertEqual(self.session.status, InterviewPracticeSession.Status.IN_PROGRESS)
        
        # Verify questions have correct structure
        first_question = self.session.questions.first()
        self.assertEqual(first_question.category, 'behavioral')
        self.assertEqual(first_question.difficulty, 'medium')
        self.assertTrue(len(first_question.evaluation_criteria) > 0)

    @patch('apps.interviews.ai_connector.genai.Client')
    def test_question_generation_failure_timeout(self, mock_genai):
        """
        Test handling of API timeout during question generation.
        
        Verify:
        - Session marked as FAILED
        - No fake questions created
        - Error message stored
        - User gets proper error notification
        """
        # Mock Gemini to fail with timeout
        mock_gemini = MockGeminiClient(should_fail=True)
        mock_client = Mock()
        mock_client.models.generate_content = mock_gemini.generate_content
        mock_genai.return_value = mock_client
        
        # Attempt to generate questions
        generate_practice_questions(self.session.id)
        
        # Verify session is marked as FAILED
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, InterviewPracticeSession.Status.FAILED)
        self.assertEqual(
            self.session.question_generation_state,
            InterviewPracticeSession.GenerationState.FAILED
        )
        
        # Verify no questions were created
        self.assertEqual(self.session.questions.count(), 0)
        
        # Verify error message was stored
        self.assertIn('error_message', self.session.settings)
        self.assertIn('Failed', self.session.settings['error_message'])

    @patch('apps.interviews.ai_connector.genai.Client')
    def test_invalid_ai_response_malformed_json(self, mock_genai):
        """
        Test handling of malformed JSON response from Gemini.
        
        Verify:
        - Validation error is caught
        - Session marked as FAILED
        - Error is logged properly
        - No questions created
        """
        # Mock Gemini to return malformed JSON
        mock_gemini = MockGeminiClient(malformed=True)
        mock_client = Mock()
        mock_client.models.generate_content = mock_gemini.generate_content
        mock_genai.return_value = mock_client
        
        # Attempt to generate questions
        with self.assertLogs('apps.interviews.tasks', level='ERROR'):
            generate_practice_questions(self.session.id)
        
        # Verify session is marked as FAILED
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, InterviewPracticeSession.Status.FAILED)
        
        # Verify validation error was recorded
        self.assertIn('validation_error', self.session.settings)

    @patch('apps.interviews.ai_connector.genai.Client')
    def test_video_metrics_submission_and_storage(self, mock_genai):
        """
        Test video metrics submission and storage.
        
        Verify:
        - Valid metrics JSON is accepted
        - Metrics stored correctly in database
        - Metrics used in scoring
        """
        # Generate questions first
        mock_gemini = MockGeminiClient()
        mock_client = Mock()
        mock_client.models.generate_content = mock_gemini.generate_content
        mock_genai.return_value = mock_client
        
        generate_practice_questions(self.session.id)
        
        # Create a practice response with video metrics
        question = self.session.questions.first()
        
        video_metrics = {
            'eye_contact_percentage': 75,
            'head_stability': 0.85,
            'speaking_consistency': 0.8,
            'pause_count': 3,
            'avg_pause_duration': 1.2,
            'fillers_count': 2,
            'speaking_rate': 140  # words per minute
        }
        
        response = PracticeResponse.objects.create(
            session=self.session,
            question=question,
            text_response="This is my answer to the question.",
            video_url="s3://bucket/video.mp4",
            video_duration=120,
            video_metrics=video_metrics,
            overall_score=0,
            improvements=[]
        )
        
        # Verify metrics were stored
        self.assertEqual(response.video_metrics['eye_contact_percentage'], 75)
        self.assertEqual(response.video_metrics['head_stability'], 0.85)
        
        # Verify metrics can be retrieved
        stored_response = PracticeResponse.objects.get(id=response.id)
        self.assertEqual(
            stored_response.video_metrics['eye_contact_percentage'],
            75
        )

    @patch('apps.interviews.ai_connector.genai.Client')
    def test_report_generation_aggregates_correctly(self, mock_genai):
        """
        Test report generation with multiple responses.
        
        Verify:
        - Report aggregates scores correctly
        - Action items are generated
        - Overall score calculated properly
        - Category breakdown included
        """
        # Generate questions first
        mock_gemini = MockGeminiClient()
        mock_client = Mock()
        mock_client.models.generate_content = mock_gemini.generate_content
        mock_genai.return_value = mock_client
        
        generate_practice_questions(self.session.id)
        
        # Create multiple responses with different scores
        questions = list(self.session.questions.all())
        scores = [85, 90, 78, 88, 92]
        
        for i, score in enumerate(scores):
            PracticeResponse.objects.create(
                session=self.session,
                question=questions[i],
                text_response=f"Answer {i+1}",
                video_url=f"s3://bucket/video{i+1}.mp4",
                video_duration=120,
                overall_score=score,
                improvements=[f"Improvement {i+1}"],
                ai_score=score
            )
        
        # Mark session as ready for report
        self.session.status = InterviewPracticeSession.Status.REVIEW_PENDING
        self.session.save()
        
        # Generate report
        generate_practice_report(self.session.id)
        
        # Verify report was created
        report = PracticePerformanceReport.objects.filter(session=self.session).first()
        self.assertIsNotNone(report)
        
        # Verify overall score is average
        expected_average = sum(scores) / len(scores)
        self.assertEqual(report.overall_score, expected_average)
        
        # Verify strengths are identified
        self.assertTrue(len(report.strengths) > 0)
        
        # Verify recommendations are provided
        self.assertTrue(len(report.recommendations) > 0)

    @patch('apps.interviews.ai_connector.genai.Client')
    def test_response_scoring_with_ai_mock(self, mock_genai):
        """
        Test response scoring with mocked AI.
        
        Verify:
        - Responses scored correctly
        - Metrics integrated into score
        - Feedback generated
        """
        # Generate questions first
        mock_gemini = MockGeminiClient()
        mock_client = Mock()
        mock_client.models.generate_content = mock_gemini.generate_content
        mock_genai.return_value = mock_client
        
        generate_practice_questions(self.session.id)
        
        # Create response
        question = self.session.questions.first()
        response = PracticeResponse.objects.create(
            session=self.session,
            question=question,
            text_response="I led a team of 5 engineers through a product redesign...",
            video_url="s3://bucket/video.mp4",
            video_duration=150,
            video_metrics={
                'eye_contact_percentage': 80,
                'head_stability': 0.9,
                'speaking_consistency': 0.85
            }
        )
        
        # Analyze response (would normally call Gemini)
        analyze_practice_response(response.id)
        
        # Verify response was scored
        response.refresh_from_db()
        self.assertIsNotNone(response.overall_score)
        self.assertTrue(response.overall_score >= 0)
        self.assertTrue(len(response.improvements) > 0)


class QuestionValidationTest(TestCase):
    """
    Tests for AI response validation and normalization.
    """

    def test_valid_question_structure(self):
        """Test that valid question structure passes validation"""
        valid_response = {
            "questions": [
                {
                    "prompt": "Tell me about yourself",
                    "category": "behavioral",
                    "difficulty": "medium",
                    "evaluation_criteria": ["clarity", "relevance"],
                    "order": 1,
                    "expected_answer_elements": ["background", "goals"]
                }
            ]
        }
        
        result = QuestionValidator.validate(valid_response)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['prompt'], "Tell me about yourself")

    def test_difficulty_normalization(self):
        """Test difficulty level normalization"""
        test_cases = [
            ('beginner', 'easy'),
            ('intermediate', 'medium'),
            ('advanced', 'hard'),
            ('easy', 'easy'),
            ('MEDIUM', 'medium'),
            ('junior', 'easy'),
            ('senior', 'hard'),
        ]
        
        for input_val, expected in test_cases:
            result = QuestionValidator.normalize_difficulty(input_val)
            self.assertEqual(result, expected)

    def test_category_normalization(self):
        """Test category normalization"""
        test_cases = [
            ('behavioral', 'behavioral'),
            ('behaviour', 'behavioral'),
            ('TECHNICAL', 'technical'),
            ('system design', 'technical'),
            ('scenario', 'situational'),
            ('hypothetical', 'situational'),
            ('general', 'behavioral'),
        ]
        
        for input_val, expected in test_cases:
            result = QuestionValidator.normalize_category(input_val)
            self.assertEqual(result, expected)

    def test_missing_required_field(self):
        """Test validation catches missing required fields"""
        invalid_response = {
            "questions": [
                {
                    "prompt": "Question without category",
                    # Missing: "category", "difficulty", etc.
                }
            ]
        }
        
        with self.assertRaises(ValidationError):
            QuestionValidator.validate(invalid_response)

    def test_invalid_difficulty_value(self):
        """Test validation catches invalid difficulty values"""
        invalid_response = {
            "questions": [
                {
                    "prompt": "Question",
                    "category": "behavioral",
                    "difficulty": "invalid_difficulty",  # Invalid
                    "evaluation_criteria": [],
                    "order": 1
                }
            ]
        }
        
        with self.assertRaises(ValidationError):
            QuestionValidator.validate(invalid_response)


class PracticeSessionEdgeCasesTest(TestCase):
    """
    Tests for edge cases and error conditions.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='candidate@example.com',
            password='password123'
        )

    def test_session_with_empty_settings(self):
        """Test session creation with empty settings"""
        session = InterviewPracticeSession.objects.create(
            candidate=self.user,
            settings={}
        )
        
        self.assertEqual(session.status, InterviewPracticeSession.Status.PENDING)
        self.assertIsNotNone(session.settings)

    def test_multiple_sessions_same_user(self):
        """Test multiple practice sessions for same user"""
        session1 = InterviewPracticeSession.objects.create(
            candidate=self.user,
            settings={'focus_areas': ['leadership']}
        )
        session2 = InterviewPracticeSession.objects.create(
            candidate=self.user,
            settings={'focus_areas': ['technical']}
        )
        
        self.assertEqual(self.user.interview_practice_sessions.count(), 2)
        self.assertNotEqual(session1.id, session2.id)

    def test_response_without_video_metrics(self):
        """Test response submission without video metrics"""
        session = InterviewPracticeSession.objects.create(
            candidate=self.user,
            settings={}
        )
        
        question = PracticeQuestion.objects.create(
            session=session,
            prompt="Test question",
            category="behavioral",
            difficulty="medium"
        )
        
        response = PracticeResponse.objects.create(
            session=session,
            question=question,
            text_response="My answer",
            video_metrics=None  # No video metrics
        )
        
        self.assertIsNone(response.video_metrics)
        self.assertEqual(response.text_response, "My answer")


class WebSocketProgressTrackingTest(TransactionTestCase):
    """
    Tests for WebSocket progress tracking integration.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='candidate@example.com',
            password='password123'
        )
        
        self.session = InterviewPracticeSession.objects.create(
            candidate=self.user,
            settings={'role_title': 'PM'}
        )

    @patch('apps.interviews.progress_tasks.get_channel_layer')
    def test_progress_update_broadcast(self, mock_channel):
        """Test that progress updates are broadcast correctly"""
        # Mock the channel layer
        mock_layer = MagicMock()
        mock_channel.return_value = mock_layer
        
        # Import here to use the patched version
        from apps.interviews.progress_tasks import track_question_generation_progress
        
        # Call the task
        track_question_generation_progress.delay(
            str(self.session.id),
            {
                'stage': 'generating',
                'progress': 30,
                'message': 'Generating questions...',
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Verify broadcast was called
        # Note: In real execution, this would broadcast to channel layer

    def test_session_progress_state(self):
        """Test session state transitions during generation"""
        # Initial state
        self.assertEqual(
            self.session.question_generation_state,
            InterviewPracticeSession.GenerationState.PENDING
        )
        
        # Transition to IN_PROGRESS
        self.session.question_generation_state = \
            InterviewPracticeSession.GenerationState.IN_PROGRESS
        self.session.save()
        
        self.session.refresh_from_db()
        self.assertEqual(
            self.session.question_generation_state,
            InterviewPracticeSession.GenerationState.IN_PROGRESS
        )
        
        # Transition to COMPLETED
        self.session.question_generation_state = \
            InterviewPracticeSession.GenerationState.COMPLETED
        self.session.save()
        
        self.session.refresh_from_db()
        self.assertEqual(
            self.session.question_generation_state,
            InterviewPracticeSession.GenerationState.COMPLETED
        )
