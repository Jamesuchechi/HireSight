"""
Middleware for automatic analytics tracking.
"""
from django.utils.deprecation import MiddlewareMixin
from .utils import get_client_ip, log_user_activity


class AnalyticsTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically track certain user actions.
    """
    
    def process_request(self, request):
        """Track request-level analytics."""
        # Store IP address in request for later use
        request.client_ip = get_client_ip(request)
        return None
    
    def process_response(self, request, response):
        """Track response-level analytics."""
        # Only track for authenticated users
        if not request.user.is_authenticated:
            return response
        
        # Track login events
        if request.path == '/accounts/login/' and response.status_code == 302:
            log_user_activity(request.user, 'login')
        
        # Track logout events
        if request.path == '/accounts/logout/':
            log_user_activity(request.user, 'logout')
        
        return response