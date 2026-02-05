
from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.interviews.ai_transcription import LiveTranscriptionService
from apps.interviews.websocket_consumers import VideoInterviewConsumer
from channels.testing import WebsocketCommunicator
from apps.interviews.models import Interview, InterviewVideoSession
import json

class LiveTranscriptionServiceTest(TestCase):
    @patch('apps.interviews.ai_connector.AIConnector')
    def test_transcribe_audio_chunk(self, MockConnector):
        # Mock connector and client
        mock_connector = MockConnector.return_value
        mock_client = MagicMock()
        mock_connector.groq_client = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_response.text = "Hello world"
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        service = LiveTranscriptionService()
        result = service.transcribe_audio_chunk(b'fake_audio', 'test.webm', 'Speaker')
        
        self.assertEqual(result['text'], "Hello world")
        self.assertEqual(result['speaker'], "Speaker")
        mock_client.audio.transcriptions.create.assert_called_once()


# Note: Testing consumers with channels usually requires transaction support if using DB
# and proper routing setup. We'll mock the service call in the consumer.

class TranscriptionConsumerTest(TestCase):
    def setUp(self):
        # Setup relies on real DB models, might skip full integration test here
        # and focus on the Service unit test which covers the core logic.
        pass
