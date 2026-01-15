"""
ASGI configuration for Django Channels with WebSocket support.
Handles real-time screening updates, AI insights, and notifications.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hiresight.settings')

# Get the Django ASGI application
django_asgi_app = get_asgi_application()

# Import routing after Django setup
from hiresight.websocket_routing import websocket_urlpatterns

# ASGI application with Channels support
application = ProtocolTypeRouter({
    # HTTP protocol
    "http": django_asgi_app,
    
    # WebSocket protocol with authentication
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
