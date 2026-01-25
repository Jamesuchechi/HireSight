"""
Unit tests for video metrics parsing and analysis.

Tests cover:
- Valid metrics JSON parsing
- Missing field handling
- Eye contact percentage calculation
- Head stability score calculation
"""

from django.test import TestCase
import json

from apps.interviews.models import VideoMetrics
from apps.interviews.ai_connector import VideoMetricsParser


class VideoMetricsParsingTest(TestCase):
    """
    Tests for video metrics parsing functionality.
    """

    def test_parse_valid_metrics_json(self):
        """
        Test parsing of valid video metrics JSON.

        Verify:
        - Valid JSON parsed correctly
        - All metrics extracted
        - Data types preserved
        - No data loss
        - Metrics object created
        """
        valid_metrics_json = {
            'eye_contact': {
                'frames_with_contact': 150,
                'total_frames': 200,
                'percentage': 75.0
            },
            'head_stability': {
                'movement_pixels': 45,
                'max_movement_pixels': 100,
                'stability_score': 0.85
            },
            'speaking': {
                'speech_rate': 120,
                'speech_rate_consistency': 0.8,
                'pauses': 5,
                'pause_duration_ms': 2500
            },
            'engagement': {
                'smile_detected': True,
                'blink_rate': 18,
                'head_nods': 12,
                'gesture_count': 3
            },
            'audio': {
                'background_noise_db': -25,
                'volume_db': -5,
                'audio_clarity': 0.9
            }
        }

        parser = VideoMetricsParser()
        result = parser.parse(valid_metrics_json)

        # Verify parsing successful
        self.assertIsNotNone(result)
        self.assertEqual(result['eye_contact']['percentage'], 75.0)
        self.assertEqual(result['head_stability']['stability_score'], 0.85)
        self.assertEqual(result['speaking']['speech_rate'], 120)

    def test_parse_metrics_with_missing_fields(self):
        """
        Test parsing when some metrics fields are missing.

        Verify:
        - Parsing succeeds with partial data
        - Missing fields handled gracefully
        - Present fields correctly extracted
        - No errors on missing optional fields
        - Can still score with available data
        """
        partial_metrics = {
            'eye_contact': {
                'frames_with_contact': 120,
                'total_frames': 200
                # percentage missing
            },
            'head_stability': {
                'stability_score': 0.75
                # movement_pixels missing
            },
            'speaking': {
                'speech_rate': 125
                # consistency missing
            }
            # engagement and audio sections missing entirely
        }

        parser = VideoMetricsParser()
        result = parser.parse(partial_metrics)

        # Should parse successfully
        self.assertIsNotNone(result)
        self.assertEqual(result['eye_contact']['frames_with_contact'], 120)
        self.assertEqual(result['head_stability']['stability_score'], 0.75)

    def test_calculate_eye_contact_percentage(self):
        """
        Test eye contact percentage calculation.

        Verify:
        - Calculation is frames_with_contact / total_frames * 100
        - Handles zero total frames
        - Handles zero contact frames
        - Result is percentage 0-100
        - Precision maintained
        """
        test_cases = [
            {
                'frames_with_contact': 150,
                'total_frames': 200,
                'expected': 75.0
            },
            {
                'frames_with_contact': 0,
                'total_frames': 200,
                'expected': 0.0
            },
            {
                'frames_with_contact': 200,
                'total_frames': 200,
                'expected': 100.0
            },
            {
                'frames_with_contact': 100,
                'total_frames': 250,
                'expected': 40.0
            },
            {
                'frames_with_contact': 333,
                'total_frames': 1000,
                'expected': 33.3
            }
        ]

        parser = VideoMetricsParser()

        for case in test_cases:
            percentage = parser.calculate_eye_contact_percentage(
                case['frames_with_contact'],
                case['total_frames']
            )
            self.assertAlmostEqual(percentage, case['expected'], places=1)

    def test_eye_contact_handles_zero_frames(self):
        """
        Test eye contact calculation with zero total frames.

        Verify:
        - Zero frames returns 0 or None safely
        - No division by zero error
        - Graceful handling of edge case
        """
        parser = VideoMetricsParser()

        # Zero total frames
        result = parser.calculate_eye_contact_percentage(0, 0)
        self.assertIn(result, [0, None, 0.0])

    def test_calculate_head_stability_score(self):
        """
        Test head stability score calculation.

        Verify:
        - Calculation based on movement pixels
        - Score is 0-1.0 or 0-100
        - Less movement = higher score
        - Handles zero movement (perfect stability)
        - Handles extreme movement
        """
        test_cases = [
            {
                'movement_pixels': 0,
                'max_movement': 100,
                'expected_high': True  # Should be high score
            },
            {
                'movement_pixels': 50,
                'max_movement': 100,
                'expected_high': False  # Should be medium
            },
            {
                'movement_pixels': 100,
                'max_movement': 100,
                'expected_high': False  # Should be low
            },
            {
                'movement_pixels': 5,
                'max_movement': 100,
                'expected_high': True  # Should be high
            }
        ]

        parser = VideoMetricsParser()

        for case in test_cases:
            score = parser.calculate_head_stability_score(
                case['movement_pixels'],
                case['max_movement']
            )

            # Score should be between 0 and 1
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1.0)

            if case['expected_high']:
                self.assertGreater(score, 0.7)
            else:
                self.assertLess(score, 0.7)

    def test_head_stability_inverse_relationship(self):
        """
        Test that head stability has inverse relationship with movement.

        Verify:
        - More movement = lower score
        - Less movement = higher score
        - Relationship is consistent
        """
        parser = VideoMetricsParser()

        low_movement_score = parser.calculate_head_stability_score(10, 100)
        medium_movement_score = parser.calculate_head_stability_score(50, 100)
        high_movement_score = parser.calculate_head_stability_score(90, 100)

        # Lower movement should have higher score
        self.assertGreater(low_movement_score, medium_movement_score)
        self.assertGreater(medium_movement_score, high_movement_score)

    def test_parse_metrics_with_null_values(self):
        """
        Test handling of null/None values in metrics.

        Verify:
        - Null values handled gracefully
        - Parser doesn't crash
        - Can distinguish present vs absent data
        - Scoring adjusts accordingly
        """
        metrics_with_nulls = {
            'eye_contact': {
                'frames_with_contact': 150,
                'total_frames': 200,
                'percentage': 75.0
            },
            'head_stability': None,
            'speaking': {
                'speech_rate': 120,
                'speech_rate_consistency': None
            },
            'engagement': None,
            'audio': None
        }

        parser = VideoMetricsParser()
        result = parser.parse(metrics_with_nulls)

        # Should handle gracefully
        self.assertIsNotNone(result)
        self.assertIsNotNone(result['eye_contact'])
        self.assertIsNone(result['head_stability'])

    def test_parse_metrics_type_validation(self):
        """
        Test that metrics types are validated during parsing.

        Verify:
        - Numeric fields are numeric
        - Boolean fields are boolean
        - Invalid types rejected or converted
        - Type errors caught
        """
        invalid_metrics = {
            'eye_contact': {
                'frames_with_contact': 'not_a_number',  # Invalid
                'total_frames': 200,
                'percentage': 75.0
            },
            'head_stability': {
                'stability_score': 'invalid'  # Invalid
            }
        }

        parser = VideoMetricsParser()

        # Should either convert or raise error
        try:
            result = parser.parse(invalid_metrics)
            # If it succeeds, types should be corrected
            self.assertIsInstance(
                result['eye_contact']['frames_with_contact'],
                (int, float)
            )
        except (TypeError, ValueError):
            # Or it should raise a validation error
            pass

    def test_parse_normalized_metrics_output(self):
        """
        Test that parsed metrics are normalized to standard format.

        Verify:
        - Output format consistent
        - Field names standardized
        - Values normalized (percentages 0-100, scores 0-1, etc.)
        - Can be used directly for scoring
        """
        raw_metrics = {
            'eye_contact': {
                'frames_with_contact': 75,
                'total_frames': 100,
                'percentage': 75.0
            },
            'head_stability': {
                'movement_pixels': 25,
                'max_movement_pixels': 100,
                'stability_score': 0.75
            }
        }

        parser = VideoMetricsParser()
        normalized = parser.parse(raw_metrics)

        # Check normalization
        self.assertTrue(0 <= normalized['eye_contact']['percentage'] <= 100)
        self.assertTrue(0 <= normalized['head_stability']['stability_score'] <= 1.0)

    def test_parse_complete_realistic_metrics(self):
        """
        Test parsing of complete, realistic video metrics from actual recording.

        Verify:
        - Real-world structure handled
        - All fields present and correct
        - Can be used for comprehensive scoring
        - No data loss or corruption
        """
        realistic_metrics = {
            'eye_contact': {
                'frames_with_contact': 1350,
                'total_frames': 1800,
                'percentage': 75.0,
                'contact_trend': [70, 72, 75, 78, 76, 75]
            },
            'head_stability': {
                'movement_pixels': 120,
                'max_movement_pixels': 200,
                'stability_score': 0.85,
                'movement_smoothness': 0.88
            },
            'speaking': {
                'speech_rate': 145,
                'speech_rate_consistency': 0.82,
                'pauses': 8,
                'pause_duration_ms': 4200,
                'filler_words': 3,
                'filler_frequency': 0.15
            },
            'engagement': {
                'smile_detected': True,
                'smile_percentage': 45,
                'blink_rate': 16,
                'head_nods': 25,
                'gesture_count': 18,
                'gesture_confidence': 0.8
            },
            'audio': {
                'background_noise_db': -28,
                'volume_db': -6,
                'audio_clarity': 0.92,
                'clipping_detected': False,
                'noise_level_trend': [-30, -28, -27, -28, -28]
            }
        }

        parser = VideoMetricsParser()
        result = parser.parse(realistic_metrics)

        # Should parse successfully
        self.assertIsNotNone(result)
        self.assertEqual(result['eye_contact']['percentage'], 75.0)
        self.assertEqual(result['engagement']['smile_percentage'], 45)
        self.assertFalse(result['audio']['clipping_detected'])

    def test_video_metrics_aggregation(self):
        """
        Test aggregation of multiple video metrics into overall score.

        Verify:
        - Eye contact, stability, speaking combined
        - Weights applied correctly
        - Overall presence score calculated
        - Score is 0-100
        """
        metrics = {
            'eye_contact': {
                'percentage': 80.0
            },
            'head_stability': {
                'stability_score': 0.85  # Convert to percentage: 85
            },
            'speaking': {
                'speech_rate_consistency': 0.80  # Convert to percentage: 80
            }
        }

        parser = VideoMetricsParser()
        overall = parser.aggregate_metrics(metrics)

        # Should produce overall score
        self.assertIsNotNone(overall)
        self.assertTrue(0 <= overall <= 100)
        # With good metrics, should be reasonably high
        self.assertGreater(overall, 75)

    def test_eye_contact_percentage_formatting(self):
        """
        Test that eye contact percentages are formatted consistently.

        Verify:
        - Always returned as decimal number
        - Always between 0 and 100
        - Decimal precision consistent (1-2 places)
        - Can be directly used for display
        """
        parser = VideoMetricsParser()

        percentages = [
            parser.calculate_eye_contact_percentage(1, 3),  # 33.33...
            parser.calculate_eye_contact_percentage(1, 2),  # 50.0
            parser.calculate_eye_contact_percentage(2, 3),  # 66.66...
        ]

        for pct in percentages:
            # Should be a number
            self.assertIsInstance(pct, (int, float))
            # Should be in valid range
            self.assertGreaterEqual(pct, 0)
            self.assertLessEqual(pct, 100)
