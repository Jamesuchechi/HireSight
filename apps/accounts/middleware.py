"""
Middleware for tracking user sessions and activity.
Add to settings.py MIDDLEWARE after SessionMiddleware and AuthenticationMiddleware.
"""

from django.utils import timezone
from django.contrib.auth import get_user
from .models import UserSession
from datetime import timedelta
import user_agents


class SessionTrackingMiddleware:
    """
    Middleware to track and manage user sessions.
    Creates UserSession records for authenticated users.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request
        if request.user.is_authenticated:
            self._track_session(request)
        
        response = self.get_response(request)
        return response
    
    def _track_session(self, request):
        """Track or update user session."""
        session_key = request.session.session_key
        
        if not session_key:
            return
        
        # Get or create UserSession
        user_session, created = UserSession.objects.get_or_create(
            session_key=session_key,
            defaults={
                'user': request.user,
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'device_type': self._get_device_type(request),
                'location': self._get_location(request),
                'expires_at': timezone.now() + timedelta(days=14),  # 2 weeks default
            }
        )
        
        # Update last activity
        if not created:
            user_session.last_activity = timezone.now()
            user_session.save(update_fields=['last_activity'])
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_device_type(self, request):
        """Detect device type from user agent."""
        user_agent_string = request.META.get('HTTP_USER_AGENT', '')
        user_agent = user_agents.parse(user_agent_string)
        
        if user_agent.is_mobile:
            return 'mobile'
        elif user_agent.is_tablet:
            return 'tablet'
        elif user_agent.is_pc:
            return 'desktop'
        else:
            return 'unknown'
    
    def _get_location(self, request):
        """
        Get approximate location from IP.
        This is a placeholder - integrate with a service like ipapi.co or GeoIP2.
        """
        # TODO: Integrate with geolocation service
        # For now, return empty string
        return ''


class CleanupExpiredSessionsMiddleware:
    """
    Middleware to periodically clean up expired UserSession records.
    Runs cleanup on every 100th request (configurable).
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_count = 0
        self.cleanup_frequency = 100  # Clean up every 100 requests
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Increment counter
        self.request_count += 1
        
        # Run cleanup periodically
        if self.request_count >= self.cleanup_frequency:
            self._cleanup_expired_sessions()
            self.request_count = 0
        
        return response
    
    def _cleanup_expired_sessions(self):
        """Delete expired UserSession records."""
        try:
            deleted_count = UserSession.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()[0]
            
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} expired sessions")
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")