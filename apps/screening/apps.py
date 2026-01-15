"""
App configuration for screening.
"""
from django.apps import AppConfig


class ScreeningConfig(AppConfig):
    """Configuration for screening app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.screening'
    verbose_name = 'AI Screening'
    
    def ready(self):
        """Import signal handlers when app is ready."""
        import apps.screening.signals  # noqa