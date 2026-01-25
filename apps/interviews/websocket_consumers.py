"""
Django Channels WebSocket Consumers for Interview Practice Sessions.
Handles real-time progress tracking for question generation and session updates.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

from .models import InterviewPracticeSession

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
