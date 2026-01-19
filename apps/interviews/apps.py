from django.apps import AppConfig


class InterviewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.interviews'
    verbose_name = 'Interview Management'
    
    def ready(self):
        """Import signals when app is ready"""
        import apps.interviews.signals