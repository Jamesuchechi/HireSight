# apps/messaging/apps.py
from django.apps import AppConfig


class MessagingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.messaging'
    verbose_name = 'Messaging System'

    def ready(self):
        """
        Import signals when the app is ready
        """
        import apps.messaging.signals
