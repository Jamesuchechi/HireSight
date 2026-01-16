from django.apps import AppConfig


class FollowingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.following'
    verbose_name = 'Following System'

    def ready(self):
        """Import signals when app is ready"""
        import apps.following.signals