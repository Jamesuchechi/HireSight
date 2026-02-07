"""
Django Channels WebSocket Consumers for real-time communication.
Handles screening progress, AI insights, notifications, and status updates.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser

from apps.screening.models import ScreeningSession, ProgressUpdate
from apps.applications.models import Application

logger = logging.getLogger(__name__)


class ScreeningProgressConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time screening progress updates.
    Replaces polling mechanism with push notifications.
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.screening_id = self.scope['url_route']['kwargs']['screening_id']
        self.user = self.scope['user']
        self.screening_group_name = f'screening_{self.screening_id}'
        
        # Verify user has access to this screening
        if not await self.user_has_screening_access(self.screening_id):
            await self.close()
            return
        
        # Join screening group
        await self.channel_layer.group_add(
            self.screening_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial screening state
        screening_data = await self.get_screening_data()
        if screening_data:
            await self.send(text_data=json.dumps({
                'type': 'screening_state',
                'data': screening_data
            }))
        
        logger.info(f'User {self.user.id} connected to screening {self.screening_id}')
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.screening_group_name,
            self.channel_name
        )
        logger.info(f'User {self.user.id} disconnected from screening {self.screening_id}')
    
    async def receive(self, text_data=None):
        """
        Receive messages from WebSocket.
        Can handle commands like request_refresh, etc.
        """
        if text_data:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_refresh':
                screening_data = await self.get_screening_data()
                await self.send(text_data=json.dumps({
                    'type': 'screening_state',
                    'data': screening_data
                }))
    
    async def progress_update(self, event):
        """
        Receive progress update from group and send to WebSocket.
        Called when another process sends to the group.
        """
        await self.send(text_data=json.dumps({
            'type': 'progress_update',
            'event': event['event'],
            'description': event['description'],
            'progress': event.get('progress'),
            'timestamp': event.get('timestamp')
        }))
    
    async def screening_complete(self, event):
        """Handle screening completion notification"""
        await self.send(text_data=json.dumps({
            'type': 'screening_complete',
            'screening_id': self.screening_id,
            'results': event.get('results'),
            'timestamp': event.get('timestamp')
        }))
    
    async def screening_error(self, event):
        """Handle screening error notification"""
        await self.send(text_data=json.dumps({
            'type': 'screening_error',
            'message': event['message'],
            'error_code': event.get('error_code')
        }))
    
    async def result_update(self, event):
        """Handle result update notification"""
        await self.send(text_data=json.dumps({
            'type': 'result_update',
            'result': event['result'],
            'timestamp': event.get('timestamp')
        }))
    
    @database_sync_to_async
    def user_has_screening_access(self, screening_id):
        """Verify user has access to this screening"""
        try:
            screening = ScreeningSession.objects.select_related('company', 'job').get(id=screening_id)
            # Check if user owns the company or is staff
            return screening.company.user == self.user or self.user.is_staff
        except ScreeningSession.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_screening_data(self):
        """Get current screening data"""
        try:
            screening = ScreeningSession.objects.select_related('job').get(id=self.screening_id)
            progress_updates = ProgressUpdate.objects.filter(
                session=screening
            ).order_by('-created_at')[:10]
            
            return {
                'screening_id': str(screening.id),
                'status': screening.status,
                'job_title': screening.job.title if screening.job else None,
                'created_at': screening.created_at.isoformat(),
                'completed_at': screening.completed_at.isoformat() if screening.completed_at else None,
                'progress_updates': [
                    {
                        'update_type': update.update_type,
                        'title': update.title,
                        'message': update.message,
                        'progress_percent': update.progress_percent,
                        'status': update.status,
                        'created_at': update.created_at.isoformat(),
                    }
                    for update in progress_updates
                ]
            }
        except ScreeningSession.DoesNotExist:
            return None


class AIInsightConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time AI insight generation.
    Streams AI analysis results as they are generated.
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.application_id = self.scope['url_route']['kwargs']['application_id']
        self.user = self.scope['user']
        self.ai_group_name = f'ai_insights_{self.application_id}'
        
        # Verify user has access
        if not await self.user_has_application_access(self.application_id):
            await self.close()
            return
        
        await self.channel_layer.group_add(
            self.ai_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f'User {self.user.id} connected to AI insights for app {self.application_id}')
    
    async def disconnect(self, close_code):
        """Handle disconnection"""
        await self.channel_layer.group_discard(
            self.ai_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data=None):
        """Handle incoming messages"""
        if text_data:
            data = json.loads(text_data)
            command = data.get('command')
            
            if command == 'generate_insight':
                await self.generate_insight(data)
    
    async def insight_generated(self, event):
        """Receive generated insight and send to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'insight',
            'insight': event['insight'],
            'score': event.get('score'),
            'timestamp': event.get('timestamp')
        }))
    
    async def insight_error(self, event):
        """Handle insight generation error"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': event['message']
        }))
    
    async def generate_insight(self, data):
        """Generate AI insight and stream results"""
        try:
            application = await self.get_application(self.application_id)
            if not application:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Application not found'
                }))
                return
            
            # Simulate AI insight generation (replace with actual service)
            await self.send(text_data=json.dumps({
                'type': 'generating',
                'message': 'AI is analyzing application...'
            }))
            
            # In production, call AIInsightService.generate_insight()
            # This would stream results back progressively
            
        except Exception as e:
            logger.error(f'Error generating insight: {e}')
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to generate insight'
            }))
    
    @database_sync_to_async
    def user_has_application_access(self, application_id):
        """Verify user access to application"""
        try:
            app = Application.objects.select_related('job', 'job__company').get(id=application_id)
            # Check if user owns the company that posted the job
            return app.job.company.user == self.user or self.user.is_staff
        except Application.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_application(self, application_id):
        """Get application data"""
        try:
            return Application.objects.get(id=application_id)
        except Application.DoesNotExist:
            return None


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for user notifications.
    Sends real-time notifications for various system events.
    """
    
    async def connect(self):
        """Handle connection"""
        self.user = self.scope['user']
        
        # Only allow authenticated users
        if self.user.is_anonymous:
            await self.close()
            return
        
        self.notification_group_name = f'notifications_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f'User {self.user.id} connected to notifications')
    
    async def disconnect(self, close_code):
        """Handle disconnection"""
        await self.channel_layer.group_discard(
            self.notification_group_name,
            self.channel_name
        )
    
    async def send_notification(self, event):
        """Send notification to user"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event['title'],
            'message': event['message'],
            'level': event.get('level', 'info'),  # info, success, warning, error
            'timestamp': event.get('timestamp'),
            'data': event.get('data', {})
        }))
    
    async def application_screened(self, event):
        """Notify user about screened application"""
        await self.send(text_data=json.dumps({
            'type': 'application_screened',
            'application_id': event['application_id'],
            'candidate_name': event['candidate_name'],
            'score': event.get('score'),
            'timestamp': event.get('timestamp')
        }))
    
    async def screening_started(self, event):
        """Notify user about screening start"""
        await self.send(text_data=json.dumps({
            'type': 'screening_started',
            'screening_id': event['screening_id'],
            'job_title': event['job_title'],
            'timestamp': event.get('timestamp')
        }))


class ApplicationStatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for application status updates.
    Real-time notifications when application status changes.
    """
    
    async def connect(self):
        """Handle connection"""
        self.application_id = self.scope['url_route']['kwargs']['application_id']
        self.user = self.scope['user']
        self.status_group_name = f'app_status_{self.application_id}'
        
        # Verify access
        if not await self.user_has_access(self.application_id):
            await self.close()
            return
        
        await self.channel_layer.group_add(
            self.status_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current status
        status_data = await self.get_application_status()
        if status_data:
            await self.send(text_data=json.dumps({
                'type': 'status_update',
                'data': status_data
            }))
    
    async def disconnect(self, close_code):
        """Handle disconnection"""
        await self.channel_layer.group_discard(
            self.status_group_name,
            self.channel_name
        )
    
    async def status_changed(self, event):
        """Handle status change"""
        await self.send(text_data=json.dumps({
            'type': 'status_changed',
            'application_id': self.application_id,
            'status': event['status'],
            'changed_by': event.get('changed_by'),
            'timestamp': event.get('timestamp'),
            'reason': event.get('reason')
        }))
    
    @database_sync_to_async
    def user_has_access(self, application_id):
        """Verify user access"""
        try:
            app = Application.objects.select_related('job', 'job__company').get(id=application_id)
            # Check if user owns the company that posted the job
            return app.job.company.user == self.user or self.user.is_staff
        except Application.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_application_status(self):
        """Get current application status"""
        try:
            app = Application.objects.get(id=self.application_id)
            return {
                'application_id': str(app.id),
                'status': app.status,
                'updated_at': app.updated_at.isoformat()
            }
        except Application.DoesNotExist:
            return None


class BulkOperationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for bulk operation progress.
    Streams progress updates during bulk screening/rejection operations.
    """
    
    async def connect(self):
        """Handle connection"""
        self.operation_id = self.scope['url_route']['kwargs']['operation_id']
        self.user = self.scope['user']
        self.operation_group_name = f'bulk_op_{self.operation_id}'
        
        await self.channel_layer.group_add(
            self.operation_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f'User {self.user.id} connected to bulk operation {self.operation_id}')
    
    async def disconnect(self, close_code):
        """Handle disconnection"""
        await self.channel_layer.group_discard(
            self.operation_group_name,
            self.channel_name
        )
    
    async def operation_progress(self, event):
        """Send operation progress update"""
        await self.send(text_data=json.dumps({
            'type': 'progress',
            'processed': event['processed'],
            'total': event['total'],
            'percentage': (event['processed'] / event['total']) * 100 if event['total'] > 0 else 0,
            'status': event.get('status'),
            'timestamp': event.get('timestamp')
        }))
    
    async def operation_complete(self, event):
        """Send operation completion"""
        await self.send(text_data=json.dumps({
            'type': 'complete',
            'operation_id': self.operation_id,
            'results': event.get('results'),
            'timestamp': event.get('timestamp')
        }))
    
    async def operation_error(self, event):
        """Send operation error"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': event['message'],
            'processed': event.get('processed'),
            'total': event.get('total')
        }))
