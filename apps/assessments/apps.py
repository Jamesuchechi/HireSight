from django.apps import AppConfig


class AssessmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.assessments'
    verbose_name = 'Skill Assessments'

    def ready(self):
        from django.db.models.signals import post_migrate

        from . import achievements
        post_migrate.connect(achievements.ensure_default_achievements, sender=self)

