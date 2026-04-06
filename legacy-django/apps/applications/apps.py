"""
Application configuration for applications app.
"""
from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    """Configuration for applications app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.applications'
    verbose_name = 'Job Applications'
    
    def ready(self):
        """Import signal handlers when app is ready."""
        import apps.applications.signals  # noqa