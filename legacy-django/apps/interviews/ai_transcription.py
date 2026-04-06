from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class LiveTranscriptionService:
    """
    Uses Groq Whisper API for real-time transcription.
    Reuses your existing Groq client setup from AIConnector.
    """
    
    def __init__(self):
        # reuse the AIConnector which already handles client initialization
        from .ai_connector import AIConnector
        self.connector = AIConnector()
        self.groq_client = self.connector.groq_client
    
    def transcribe_audio_chunk(self, audio_data, filename='audio.webm', speaker='Candidate'):
        """
        Transcribe a chunk of audio.
        
        Args:
            audio_data (bytes): The raw audio bytes (or file-like object)
            filename (str): Filename with extension (e.g. 'chunk.webm')
            speaker (str): Name of the speaker
            
        Returns:
            dict: {
                'text': str, 
                'speaker': str, 
                'timestamp': str,
                'error': str (optional)
            }
        """
        if not self.groq_client:
            return {'error': 'Groq client not available'}
        
        try:
            # We must pass a tuple of (filename, file_content, content_type) to the client
            # The client usually expects a file-like object or bytes.
            audio_file = (filename, audio_data)
            
            # Use Groq's transcription API (Whisper)
            # Make sure this call is async-compatible or wrap it if strictly sync.
            # However, standard python clients are often sync. 
            # In an async consumer, we might need sync_to_async or run_in_executor if this blocks.
            # But the 'groq' lib might have async support or we rely on partial blocking for now.
            # Best practice: use run_in_executor for network calls in async context.
            
            # Since we are likely running this inside an async consumer, we should offload it.
            # But for simplicity in this class, we define the logic. The consumer will wrap it.
            
            # Note: The groq client call is synchronous by default unless using AsyncGroq.
            # AIConnector uses sync 'Groq'.
            
            response = self.groq_client.audio.transcriptions.create(
                model='whisper-large-v3',
                file=audio_file,
                language='en',
                response_format='json'
            )
            
            text = response.text.strip()
            
            return {
                'text': text,
                'speaker': speaker,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f'Transcription error: {e}')
            return {'error': str(e)}
