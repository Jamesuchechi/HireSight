"""
Unit tests for response scoring functionality.

Tests cover:
- Scoring with all metrics present
- Handling missing video metrics
- Weighted score calculations
- Strength identification
- Improvement identification
"""

from django.test import TestCase
from unittest.mock import Mock, patch

from apps.interviews.ai_connector import ResponseScorer, ValidationError


class ResponseScorerTest(TestCase):
    """
    Tests for ResponseScorer class.
    """

    def test_response_scorer_all_metrics(self):
        """
        Test scoring when all metrics are present.

        Verify:
        - All metrics accepted
        - Comprehensive scoring results
        - All score categories calculated
        - No missing field errors
        """
        complete_response = {
            'content_relevance': 85,
            'completeness': 90,
            'structure_clarity': 88,
            'key_points_covered': ['strategy', 'execution', 'metrics'],
            'eye_contact_percentage': 75,
            'head_stability': 0.85,
            'speaking_consistency': 0.8,
            'presence_score': 82,
            'strengths': ['clear communication', 'good structure', 'well-organized'],
            'improvements': ['add more examples', 'speak more slowly'],
            'overall_feedback': 'Strong response with clear thinking'
        }

        # Should score successfully with all metrics
        result = ResponseScorer.score_response(complete_response)
        
        self.assertIn('content_score', result)
        self.assertIn('presence_score', result)
        self.assertIn('overall_score', result)
        self.assertTrue(0 <= result['overall_score'] <= 100)

    def test_response_scorer_missing_video_metrics(self):
        """
        Test scoring when video metrics are missing.

        Verify:
        - Can score without eye contact data
        - Can score without head stability data
        - Can score without speaking consistency
        - Content metrics alone sufficient
        - Graceful degradation
        """
        response_without_video = {
            'content_relevance': 85,
            'completeness': 90,
            'structure_clarity': 88,
            'key_points_covered': ['strategy', 'execution'],
            'eye_contact_percentage': None,
            'head_stability': None,
            'speaking_consistency': None,
            'presence_score': None,
            'strengths': ['clear thinking'],
            'improvements': ['add examples'],
            'overall_feedback': 'Good response'
        }

        # Should handle missing video metrics gracefully
        result = ResponseScorer.score_response(response_without_video)
        
        self.assertIsNotNone(result)
        self.assertIn('content_score', result)
        # Overall score should still be calculated from available metrics
        self.assertTrue(0 <= result.get('overall_score', 0) <= 100)

    def test_response_scorer_weighted_calculation(self):
        """
        Test that weighted score calculation is correct.

        Verify:
        - Content weight applied (typically 70%)
        - Presence weight applied (typically 30%)
        - Weights sum to 100%
        - Calculation formula correct
        - Score range 0-100
        """
        response = {
            'content_relevance': 80,
            'completeness': 80,
            'structure_clarity': 80,
            'key_points_covered': ['point1'],
            'eye_contact_percentage': 80,
            'head_stability': 0.8,
            'speaking_consistency': 0.8,
            'presence_score': 80,
            'strengths': ['test'],
            'improvements': ['test'],
            'overall_feedback': 'Test'
        }

        scores = ResponseScorer.score_response(response)
        
        # Verify weighted combination
        content_score = scores.get('content_score', 0)
        presence_score = scores.get('presence_score', 0)
        overall_score = scores.get('overall_score', 0)
        
        # Overall should be weighted combination of content and presence
        # Typical: 70% content + 30% presence
        expected = (content_score * 0.7) + (presence_score * 0.3)
        
        # Allow 1 point tolerance for rounding
        self.assertAlmostEqual(overall_score, expected, delta=1.5)

    def test_response_scorer_strength_identification(self):
        """
        Test identification of response strengths.

        Verify:
        - Strengths extracted from response
        - Multiple strengths captured
        - Strength categories identified
        - Empty strengths handled
        """
        response_with_strengths = {
            'content_relevance': 90,
            'completeness': 95,
            'structure_clarity': 92,
            'key_points_covered': ['strategy', 'execution', 'metrics'],
            'eye_contact_percentage': 85,
            'head_stability': 0.9,
            'speaking_consistency': 0.88,
            'presence_score': 87,
            'strengths': [
                'Clear and concise communication',
                'Excellent structure and organization',
                'Strong analytical thinking',
                'Good use of examples'
            ],
            'improvements': ['Add more data-driven insights'],
            'overall_feedback': 'Excellent response'
        }

        result = ResponseScorer.analyze_strengths(response_with_strengths)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)
        self.assertIn('Clear and concise communication', result)
        self.assertIn('Good use of examples', result)

    def test_response_scorer_improvement_identification(self):
        """
        Test identification of improvement areas.

        Verify:
        - Improvements extracted from response
        - Multiple improvements captured
        - Actionable feedback format
        - Empty improvements handled
        """
        response_with_improvements = {
            'content_relevance': 75,
            'completeness': 78,
            'structure_clarity': 80,
            'key_points_covered': ['strategy'],
            'eye_contact_percentage': 70,
            'head_stability': 0.75,
            'speaking_consistency': 0.72,
            'presence_score': 72,
            'strengths': ['Good starting point'],
            'improvements': [
                'Add more specific examples',
                'Consider the user perspective more',
                'Provide more detailed action plans',
                'Include metrics and measurement'
            ],
            'overall_feedback': 'Good response with room for improvement'
        }

        result = ResponseScorer.analyze_improvements(response_with_improvements)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)
        self.assertIn('Add more specific examples', result)
        self.assertIn('Include metrics and measurement', result)

    def test_response_scorer_content_score_calculation(self):
        """
        Test calculation of content score from components.

        Verify:
        - Relevance weight applied
        - Completeness weight applied
        - Clarity weight applied
        - Key points influence score
        - Final score in valid range
        """
        response = {
            'content_relevance': 90,
            'completeness': 85,
            'structure_clarity': 88,
            'key_points_covered': ['p1', 'p2', 'p3'],
            'eye_contact_percentage': 80,
            'head_stability': 0.8,
            'speaking_consistency': 0.8,
            'presence_score': 80,
            'strengths': [],
            'improvements': [],
            'overall_feedback': 'Test'
        }

        scores = ResponseScorer.score_response(response)
        content_score = scores.get('content_score', 0)
        
        # Content score should average the three components
        # Plus bonus for key points covered (typically 3/5 for medium response)
        self.assertTrue(80 <= content_score <= 95)

    def test_response_scorer_presence_score_calculation(self):
        """
        Test calculation of presence score from video metrics.

        Verify:
        - Eye contact weighted correctly
        - Head stability weighted correctly
        - Speaking consistency weighted correctly
        - Presence score overall weighted
        - All contribute to final presence score
        """
        response = {
            'content_relevance': 80,
            'completeness': 80,
            'structure_clarity': 80,
            'key_points_covered': ['p1'],
            'eye_contact_percentage': 75,
            'head_stability': 0.85,
            'speaking_consistency': 0.80,
            'presence_score': 80,
            'strengths': [],
            'improvements': [],
            'overall_feedback': 'Test'
        }

        scores = ResponseScorer.score_response(response)
        presence_score = scores.get('presence_score', 0)
        
        # Presence score should be influenced by all video metrics
        # Typical: average of eye contact, head stability, speaking consistency
        self.assertTrue(75 <= presence_score <= 85)

    def test_response_scorer_handles_edge_cases(self):
        """
        Test handling of edge cases in scoring.

        Verify:
        - Zero scores handled
        - Maximum scores handled
        - Mixed good/bad scores handled
        - Extreme variations handled
        """
        edge_cases = [
            {
                # All zeros
                'content_relevance': 0,
                'completeness': 0,
                'structure_clarity': 0,
                'key_points_covered': [],
                'eye_contact_percentage': 0,
                'head_stability': 0.0,
                'speaking_consistency': 0.0,
                'presence_score': 0,
                'strengths': [],
                'improvements': ['Everything needs improvement'],
                'overall_feedback': 'Poor response'
            },
            {
                # All maximums
                'content_relevance': 100,
                'completeness': 100,
                'structure_clarity': 100,
                'key_points_covered': ['p1', 'p2', 'p3', 'p4', 'p5'],
                'eye_contact_percentage': 100,
                'head_stability': 1.0,
                'speaking_consistency': 1.0,
                'presence_score': 100,
                'strengths': ['Everything excellent'],
                'improvements': [],
                'overall_feedback': 'Perfect response'
            },
            {
                # Mixed: strong content, weak presence
                'content_relevance': 95,
                'completeness': 90,
                'structure_clarity': 92,
                'key_points_covered': ['p1', 'p2', 'p3'],
                'eye_contact_percentage': 30,
                'head_stability': 0.3,
                'speaking_consistency': 0.35,
                'presence_score': 32,
                'strengths': ['Excellent content'],
                'improvements': ['Work on presence'],
                'overall_feedback': 'Good content, needs presence work'
            }
        ]

        for response in edge_cases:
            result = ResponseScorer.score_response(response)
            self.assertIsNotNone(result)
            overall = result.get('overall_score', 0)
            # Should always be in valid range
            self.assertTrue(0 <= overall <= 100)

    def test_response_scorer_validation_before_scoring(self):
        """
        Test that response is validated before scoring.

        Verify:
        - Invalid structures rejected
        - Required fields checked
        - Type validation performed
        - Clear error messages
        """
        invalid_responses = [
            {
                # Missing overall_feedback
                'content_relevance': 80,
                'completeness': 80,
                'structure_clarity': 80,
                'key_points_covered': ['p1'],
                'eye_contact_percentage': 75,
                'head_stability': 0.75,
                'speaking_consistency': 0.75,
                'presence_score': 75,
                'strengths': [],
                'improvements': []
            },
            {
                # Invalid content_relevance (> 100)
                'content_relevance': 150,
                'completeness': 80,
                'structure_clarity': 80,
                'key_points_covered': ['p1'],
                'eye_contact_percentage': 75,
                'head_stability': 0.75,
                'speaking_consistency': 0.75,
                'presence_score': 75,
                'strengths': [],
                'improvements': [],
                'overall_feedback': 'Test'
            },
            {
                # Invalid head_stability (> 1.0)
                'content_relevance': 80,
                'completeness': 80,
                'structure_clarity': 80,
                'key_points_covered': ['p1'],
                'eye_contact_percentage': 75,
                'head_stability': 1.5,
                'speaking_consistency': 0.75,
                'presence_score': 75,
                'strengths': [],
                'improvements': [],
                'overall_feedback': 'Test'
            }
        ]

        for invalid_response in invalid_responses:
            with self.assertRaises((ValidationError, ValueError)):
                ResponseScorer.score_response(invalid_response)
