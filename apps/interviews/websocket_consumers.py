"""
Django Channels WebSocket Consumers for Interview Practice Sessions.
Handles real-time progress tracking for question generation and session updates.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.utils import timezone
import base64

from .models import InterviewPracticeSession
from .ai_transcription import LiveTranscriptionService

logger = logging.getLogger(__name__)


class SessionProgressConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time practice session progress updates.
    Broadcasts question generation progress, session state changes, and user actions.
    
    Usage:
        Connect to: ws://localhost/ws/interview/session/<session_id>/
        Receives: Progress updates, generation status, session events
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.user = self.scope['user']
        self.session_group_name = f'session_{self.session_id}'
        
        # Verify user has access to this session
        if not await self.user_has_session_access(self.session_id):
            await self.close()
            return
        
        # Join session group
        await self.channel_layer.group_add(
            self.session_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial session state
        session_data = await self.get_session_data()
        if session_data:
            await self.send(text_data=json.dumps({
                'type': 'session_state',
                'data': session_data,
                'timestamp': timezone.now().isoformat()
            }))
        
        logger.info(f'User {self.user.id} connected to session {self.session_id}')
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.session_group_name,
            self.channel_name
        )
        logger.info(f'User {self.user.id} disconnected from session {self.session_id}')
    
    async def receive(self, text_data=None):
        """
        Receive messages from WebSocket.
        Can handle commands like request_refresh, etc.
        """
        if text_data:
            try:
                data = json.loads(text_data)
                message_type = data.get('type')
                
                if message_type == 'request_refresh':
                    session_data = await self.get_session_data()
                    await self.send(text_data=json.dumps({
                        'type': 'session_state',
                        'data': session_data,
                        'timestamp': timezone.now().isoformat()
                    }))
                else:
                    logger.debug(f'Unknown message type: {message_type}')
            except json.JSONDecodeError:
                logger.error('Invalid JSON received')
    
    async def progress_update(self, event):
        """
        Receive progress update from group and send to WebSocket.
        Triggered by progress_tasks.track_question_generation_progress()
        """
        await self.send(text_data=json.dumps({
            'type': 'progress_update',
            'stage': event.get('stage'),
            'message': event.get('message'),
            'progress': event.get('progress', 0),
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))
    
    async def session_update(self, event):
        """
        Receive session update from group and send to WebSocket.
        Triggered by progress_tasks.broadcast_session_update()
        """
        await self.send(text_data=json.dumps({
            'type': 'session_update',
            'update_type': event.get('update_type'),
            'data': event.get('data'),
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))
    
    @database_sync_to_async
    def user_has_session_access(self, session_id):
        """Verify user has access to this session"""
        try:
            session = InterviewPracticeSession.objects.get(id=session_id)
            # User must be the session candidate
            return session.candidate == self.user
        except InterviewPracticeSession.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_session_data(self):
        """Get current session state"""
        try:
            session = InterviewPracticeSession.objects.get(id=self.session_id)
            return {
                'session_id': str(session.id),
                'status': session.status,
                'question_generation_state': session.question_generation_state,
                'report_generation_state': session.report_generation_state,
                'total_questions': session.questions.count(),
                'completed_questions': session.questions.filter(
                    responses__isnull=False
                ).distinct().count(),
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'started_at': session.started_at.isoformat() if session.started_at else None,
            }
        except InterviewPracticeSession.DoesNotExist:
            return None


class VideoInterviewConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time video interview signaling and coordination.
    Handles:
    - WebRTC Signaling (Offer, Answer, ICE Candidates)
    - Room Presence (Peer Joined/Left)
    - Live Features (Notes, Rating, Transcript)
    """

    async def connect(self):
        self.interview_id = self.scope['url_route']['kwargs']['interview_id']
        self.user = self.scope['user']
        self.room_group_name = f'interview_{self.interview_id}'
        
        # Verify user access
        if not await self.user_has_interview_access(self.interview_id):
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Notify room of user join
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'peer_status',
                'status': 'joined',
                'user_id': self.user.id,
                'email': self.user.email,
                'sender_channel_name': self.channel_name
            }
        )
        
        # Log session start if not already logged
        await self.log_session_join()

    async def disconnect(self, close_code):
        # Notify room of user leave
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'peer_status',
                'status': 'left',
                'user_id': self.user.id,
                'sender_channel_name': self.channel_name
            }
        )

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        # Signaling Messages (Relay to other peers)
        if message_type in ['offer', 'answer', 'candidate']:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'signaling_message',
                    'message': data,
                    'sender_channel_name': self.channel_name
                }
            )
        
        # Live Interview Tools
        elif message_type == 'update_notes':
            # Save notes to DB (Company only)
            if self.user.account_type == 'company':
                await self.save_interview_notes(data.get('notes'))
        
        elif message_type == 'update_rating':
            # Save rating (Company only)
            if self.user.account_type == 'company':
                await self.save_interview_rating(data.get('rating'))
        
        elif message_type == 'transcript_chunk':
            # Broadcast transcript to both parties
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'transcript_update',
                    'text': data.get('text'),
                    'sender': data.get('speaker_name', 'Unknown')
                }
            )
            # Persist transcript
            await self.append_transcript(data.get('text'), data.get('speaker_name'))

        elif message_type == 'code_update':
            # Broadcast code update to others
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'code_update_message',
                    'code': data.get('code'),
                    'language': data.get('language'),
                    'from_user': data.get('from_user'),
                    'sender_channel_name': self.channel_name
                }
            )

    # Handlers for Group Messages
    async def signaling_message(self, event):
        # Don't echo back to sender
        if self.channel_name != event['sender_channel_name']:
            await self.send(text_data=json.dumps(event['message']))

    async def code_update_message(self, event):
        # Send code update to client if they are not the sender
        if self.channel_name != event.get('sender_channel_name'):
            await self.send(text_data=json.dumps({
                'type': 'code_update',
                'code': event['code'],
                'language': event['language'],
                'from_user': event['from_user']
            }))

    async def peer_status(self, event):
        if self.channel_name != event['sender_channel_name']:
            await self.send(text_data=json.dumps({
                'type': 'peer_status',
                'status': event['status'],
                'user_id': event.get('user_id'),
                'email': event.get('email')
            }))

    async def transcript_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'transcript_update',
            'text': event['text'],
            'sender': event['sender']
        }))

    # Database Operations
    @database_sync_to_async
    def user_has_interview_access(self, interview_id):
        from .models import Interview
        try:
            interview = Interview.objects.get(id=interview_id)
            if self.user.account_type == 'company':
                return interview.application.job.company.user == self.user
            elif self.user.account_type == 'personal':
                return interview.application.applicant == self.user
            return False
        except Interview.DoesNotExist:
            return False

    @database_sync_to_async
    def log_session_join(self):
        from .models import Interview, InterviewVideoSession
        try:
            # Ensure DB connection is active
            from django.db import connection
            connection.close()
            
            interview = Interview.objects.get(id=self.interview_id)
            session, created = InterviewVideoSession.objects.get_or_create(
                interview=interview,
                defaults={'room_name': f'room_{self.interview_id}'}
            )
            
            now = timezone.now()
            if self.user.account_type == 'company':
                session.company_joined_at = now
            else:
                session.candidate_joined_at = now
                
            if not session.started_at and session.company_joined_at and session.candidate_joined_at:
                session.started_at = now
                
            session.save()
        except Exception as e:
            logger.error(f"Error logging session join: {e}")

    @database_sync_to_async
    def save_interview_notes(self, notes):
        from .models import InterviewVideoSession
        try:
            # Ensure DB connection is active
            from django.db import connection
            connection.close()

            session = InterviewVideoSession.objects.get(interview_id=self.interview_id)
            session.internal_notes = notes
            session.save(update_fields=['internal_notes'])
        except Exception as e:
            logger.error(f"Error saving notes: {e}")

    @database_sync_to_async
    def save_interview_rating(self, rating):
        from .models import InterviewVideoSession
        try:
             # Ensure DB connection is active
            from django.db import connection
            connection.close()

            VideoSession = InterviewVideoSession.objects.get(interview_id=self.interview_id)
            # Logic to update engagement score or call main interview rating update
            # Here we map it to engagement score for now, or update the main interview rating
            VideoSession.candidate_engagement_score = rating # Placeholder logic
            VideoSession.save(update_fields=['candidate_engagement_score'])
            
            # Also update main interview rating
            interview = VideoSession.interview
            interview.interview_rating = int(float(rating))
            interview.save(update_fields=['interview_rating'])
        except Exception as e:
            logger.error(f"Error saving rating: {e}")

    @database_sync_to_async
    def append_transcript(self, text, speaker):
        from .models import InterviewVideoSession
        try:
             # Ensure DB connection is active
            from django.db import connection
            connection.close()

            session = InterviewVideoSession.objects.get(interview_id=self.interview_id)
            timestamp = timezone.now().strftime("%H:%M:%S")
            line = f"[{timestamp}] {speaker}: {text}\n"
            session.transcript += line
            session.save(update_fields=['transcript'])
        except Exception as e:
             logger.error(f"Error appending transcript: {e}")

    async def handle_audio_transcription(self, audio_base64, speaker_name):
        """Process audio chunk and broadcast transcript"""
        try:
            # Decode base64
            if ',' in audio_base64:
                header, encoded = audio_base64.split(',', 1)
            else:
                encoded = audio_base64
                
            audio_bytes = base64.b64decode(encoded)
            
            # Initialize service (lazy load)
            if not hasattr(self, 'transcription_service'):
                self.transcription_service = LiveTranscriptionService()
            
            # Run transcription in thread
            result = await sync_to_async(self.transcription_service.transcribe_audio_chunk)(
                audio_bytes, 
                'chunk.webm', 
                speaker_name
            )
            
            if result.get('text'):
                # Broadcast transcript
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'transcript_update',
                        'text': result['text'],
                        'sender': speaker_name
                    }
                )
                
                # Persist to DB
                await self.append_transcript(result['text'], speaker_name)
                
        except Exception as e:
            logger.error(f"Error processing audio: {e}")




