"""
WebSocket utility service for sending real-time updates from Django.
Provides async methods to broadcast messages to connected clients.
"""

import asyncio
import json
import logging
from channels.layers import get_channel_layer
from django.utils import timezone

logger = logging.getLogger(__name__)


class WebSocketService:
    """Service for sending WebSocket messages to clients"""
    
    @staticmethod
    async def send_screening_progress(screening_id, event, description, progress=None):
        """
        Send progress update for screening
        
        Args:
            screening_id: UUID of screening
            event: Event type/name
            description: Human-readable description
            progress: Percentage progress (0-100)
        """
        channel_layer = get_channel_layer()
        group_name = f'screening_{screening_id}'
        
        try:
            await channel_layer.group_send(
                group_name,
                {
                    'type': 'progress_update',
                    'event': event,
                    'description': description,
                    'progress': progress,
                    'timestamp': timezone.now().isoformat()
                }
            )
            logger.info(f'Sent progress update to {group_name}: {event}')
        except Exception as e:
            logger.error(f'Failed to send progress update to {group_name}: {e}')
    
    @staticmethod
    async def send_screening_complete(screening_id, results=None):
        """
        Notify clients that screening is complete
        
        Args:
            screening_id: UUID of screening
            results: Screening results data
        """
        channel_layer = get_channel_layer()
        group_name = f'screening_{screening_id}'
        
        try:
            await channel_layer.group_send(
                group_name,
                {
                    'type': 'screening_complete',
                    'screening_id': str(screening_id),
                    'results': results,
                    'timestamp': timezone.now().isoformat()
                }
            )
            logger.info(f'Sent screening complete to {group_name}')
        except Exception as e:
            logger.error(f'Failed to send screening complete to {group_name}: {e}')
    
    @staticmethod
    async def send_screening_error(screening_id, message, error_code=None):
        """
        Notify clients of screening error
        
        Args:
            screening_id: UUID of screening
            message: Error message
            error_code: Optional error code
        """
        channel_layer = get_channel_layer()
        group_name = f'screening_{screening_id}'
        
        try:
            await channel_layer.group_send(
                group_name,
                {
                    'type': 'screening_error',
                    'message': message,
                    'error_code': error_code
                }
            )
            logger.error(f'Sent screening error to {group_name}: {message}')
        except Exception as e:
            logger.error(f'Failed to send screening error to {group_name}: {e}')
    
    @staticmethod
    async def send_ai_insight(application_id, insight, score=None):
        """
        Send AI insight to clients
        
        Args:
            application_id: UUID of application
            insight: Insight data/text
            score: Optional insight score
        """
        channel_layer = get_channel_layer()
        group_name = f'ai_insights_{application_id}'
        
        try:
            await channel_layer.group_send(
                group_name,
                {
                    'type': 'insight_generated',
                    'insight': insight,
                    'score': score,
                    'timestamp': timezone.now().isoformat()
                }
            )
            logger.info(f'Sent AI insight to {group_name}')
        except Exception as e:
            logger.error(f'Failed to send AI insight to {group_name}: {e}')
    
    @staticmethod
    async def send_notification(user_id, title, message, level='info', data=None):
        """
        Send notification to specific user
        
        Args:
            user_id: User ID
            title: Notification title
            message: Notification message
            level: Log level (info, success, warning, error)
            data: Additional data
        """
        channel_layer = get_channel_layer()
        group_name = f'notifications_{user_id}'
        
        try:
            await channel_layer.group_send(
                group_name,
                {
                    'type': 'send_notification',
                    'title': title,
                    'message': message,
                    'level': level,
                    'data': data or {},
                    'timestamp': timezone.now().isoformat()
                }
            )
            logger.info(f'Sent notification to user {user_id}: {title}')
        except Exception as e:
            logger.error(f'Failed to send notification to user {user_id}: {e}')
    
    @staticmethod
    async def send_application_screened(user_id, application_id, candidate_name, score):
        """
        Notify user that application was screened
        
        Args:
            user_id: User ID
            application_id: Application ID
            candidate_name: Candidate name
            score: Screening score
        """
        channel_layer = get_channel_layer()
        group_name = f'notifications_{user_id}'
        
        try:
            await channel_layer.group_send(
                group_name,
                {
                    'type': 'application_screened',
                    'application_id': str(application_id),
                    'candidate_name': candidate_name,
                    'score': score,
                    'timestamp': timezone.now().isoformat()
                }
            )
            logger.info(f'Sent application screened notification to user {user_id}')
        except Exception as e:
            logger.error(f'Failed to send application screened notification: {e}')
    
    @staticmethod
    async def send_application_status_change(application_id, status, changed_by=None, reason=None):
        """
        Notify clients of application status change
        
        Args:
            application_id: Application ID
            status: New status
            changed_by: User who made the change
            reason: Reason for change
        """
        channel_layer = get_channel_layer()
        group_name = f'app_status_{application_id}'
        
        try:
            await channel_layer.group_send(
                group_name,
                {
                    'type': 'status_changed',
                    'application_id': str(application_id),
                    'status': status,
                    'changed_by': changed_by,
                    'reason': reason,
                    'timestamp': timezone.now().isoformat()
                }
            )
            logger.info(f'Sent status change to {group_name}: {status}')
        except Exception as e:
            logger.error(f'Failed to send status change to {group_name}: {e}')
    
    @staticmethod
    async def send_bulk_operation_progress(operation_id, processed, total, status=None):
        """
        Send bulk operation progress update
        
        Args:
            operation_id: Bulk operation ID
            processed: Number processed
            total: Total number
            status: Current status message
        """
        channel_layer = get_channel_layer()
        group_name = f'bulk_op_{operation_id}'
        
        try:
            await channel_layer.group_send(
                group_name,
                {
                    'type': 'operation_progress',
                    'processed': processed,
                    'total': total,
                    'status': status,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f'Failed to send bulk operation progress to {group_name}: {e}')
    
    @staticmethod
    async def send_bulk_operation_complete(operation_id, results=None):
        """
        Notify clients that bulk operation completed
        
        Args:
            operation_id: Bulk operation ID
            results: Operation results
        """
        channel_layer = get_channel_layer()
        group_name = f'bulk_op_{operation_id}'
        
        try:
            await channel_layer.group_send(
                group_name,
                {
                    'type': 'operation_complete',
                    'operation_id': str(operation_id),
                    'results': results,
                    'timestamp': timezone.now().isoformat()
                }
            )
            logger.info(f'Sent bulk operation complete to {group_name}')
        except Exception as e:
            logger.error(f'Failed to send bulk operation complete to {group_name}: {e}')
    
    @staticmethod
    async def send_bulk_operation_error(operation_id, message, processed=None, total=None):
        """
        Notify clients of bulk operation error
        
        Args:
            operation_id: Bulk operation ID
            message: Error message
            processed: Number processed before error
            total: Total number
        """
        channel_layer = get_channel_layer()
        group_name = f'bulk_op_{operation_id}'
        
        try:
            await channel_layer.group_send(
                group_name,
                {
                    'type': 'operation_error',
                    'message': message,
                    'processed': processed,
                    'total': total
                }
            )
            logger.error(f'Sent bulk operation error to {group_name}: {message}')
        except Exception as e:
            logger.error(f'Failed to send bulk operation error to {group_name}: {e}')


class SyncWebSocketService:
    """
    Synchronous wrapper for WebSocket service.
    Use in Django views/tasks that don't support async.
    """
    
    @staticmethod
    def send_screening_progress_sync(screening_id, event, description, progress=None):
        """Synchronous wrapper for send_screening_progress"""
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                WebSocketService.send_screening_progress(
                    screening_id, event, description, progress
                )
            )
        finally:
            loop.close()
    
    @staticmethod
    def send_notification_sync(user_id, title, message, level='info', data=None):
        """Synchronous wrapper for send_notification"""
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                WebSocketService.send_notification(
                    user_id, title, message, level, data
                )
            )
        finally:
            loop.close()
    
    @staticmethod
    def send_bulk_operation_progress_sync(operation_id, processed, total, status=None):
        """Synchronous wrapper for send_bulk_operation_progress"""
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                WebSocketService.send_bulk_operation_progress(
                    operation_id, processed, total, status
                )
            )
        finally:
            loop.close()
