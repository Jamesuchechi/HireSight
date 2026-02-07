"""
WebSocket URL routing configuration for Django Channels.
Maps WebSocket endpoints to consumer classes.
"""

from django.urls import re_path
from apps.messaging import consumers as messaging_consumers
from apps.screening import websocket_consumers
from apps.interviews import websocket_consumers as interviews_consumers

# WebSocket URL patterns
websocket_urlpatterns = [
    # Interview practice session progress
    re_path(
        r'ws/interview/session/(?P<session_id>[0-9a-f-]+)/$',
        interviews_consumers.SessionProgressConsumer.as_asgi(),
        name='ws_session_progress'
    ),
    
    # Real-time Video Interview Room
    re_path(
        r'ws/interview/room/(?P<interview_id>[0-9a-f-]+)/$',
        interviews_consumers.VideoInterviewConsumer.as_asgi(),
        name='ws_interview_room'
    ),
    
    # Screening progress updates
    re_path(
        r'ws/screening/(?P<screening_id>[0-9a-f-]+)/$',
        websocket_consumers.ScreeningProgressConsumer.as_asgi(),
        name='ws_screening_progress'
    ),
    
    # AI insights real-time updates
    re_path(
        r'ws/ai-insights/(?P<application_id>[0-9a-f-]+)/$',
        websocket_consumers.AIInsightConsumer.as_asgi(),
        name='ws_ai_insights'
    ),
    
    # Notifications for authenticated users
    re_path(
        r'ws/notifications/$',
        websocket_consumers.NotificationConsumer.as_asgi(),
        name='ws_notifications'
    ),
    
    # Application status updates
    re_path(
        r'ws/application/(?P<application_id>[0-9a-f-]+)/$',
        websocket_consumers.ApplicationStatusConsumer.as_asgi(),
        name='ws_application_status'
    ),
    
    # Bulk operations progress
    re_path(
        r'ws/bulk-operation/(?P<operation_id>[0-9a-f-]+)/$',
        websocket_consumers.BulkOperationConsumer.as_asgi(),
        name='ws_bulk_operation'
    ),

    re_path(
        r'ws/messaging/conversation/(?P<conversation_id>[0-9a-f-]+)/$',
        messaging_consumers.ConversationConsumer.as_asgi(),
        name='ws_conversation'
    ),
    re_path(
        r'ws/messaging/unread/$',
        messaging_consumers.UnreadConsumer.as_asgi(),
        name='ws_unread'
    ),
]
