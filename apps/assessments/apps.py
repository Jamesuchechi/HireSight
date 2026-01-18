from django.apps import AppConfig


class AssessmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.assessments'
    verbose_name = 'Skill Assessments'

    def ready(self):
        from . import achievements  # noqa: F401
        achievements.ensure_default_achievements()
