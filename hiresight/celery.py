"""
Celery configuration for HireSight project.
This module initializes Celery and configures it to work with Django.
"""
import os
from celery import Celery
from celery.signals import task_failure, task_success, worker_ready
import logging

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hiresight.settings')

# Create Celery app
app = Celery('hiresight')

# Load configuration from Django settings
# The namespace='CELERY' means all celery-related config keys should be prefixed with 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Configure logger
logger = logging.getLogger(__name__)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')


@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **other_kwargs):
    """
    Handle task failures by logging them
    """
    logger.error(
        f'Task {sender.name}[{task_id}] failed with exception: {exception}',
        exc_info=einfo,
        extra={
            'task_id': task_id,
            'task_name': sender.name if sender else 'Unknown',
            'args': args,
            'kwargs': kwargs,
        }
    )


@task_success.connect
def handle_task_success(sender=None, result=None, **kwargs):
    """
    Handle successful task completion
    """
    logger.info(f'Task {sender.name} completed successfully')


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """
    Log when Celery worker is ready
    """
    logger.info('Celery worker is ready and waiting for tasks')


# Configure task routes (optional - for organizing tasks into different queues)
app.conf.task_routes = {
    # Email tasks - high priority
    'apps.interviews.tasks.send_interview_invitation': {'queue': 'emails'},
    'apps.interviews.tasks.send_interview_cancellation': {'queue': 'emails'},
    'apps.interviews.tasks.send_interview_reminders': {'queue': 'emails'},
    
    # Cleanup tasks - low priority
    'apps.interviews.tasks.cleanup_old_interviews': {'queue': 'cleanup'},
    'apps.screening.tasks.cleanup_old_screening_files': {'queue': 'cleanup'},
    'apps.applications.tasks.cleanup_old_applications': {'queue': 'cleanup'},
    'apps.assessments.tasks.cleanup_expired_attempts': {'queue': 'cleanup'},
    
    # Analytics tasks - separate queue
    'apps.analytics.tasks.*': {'queue': 'analytics'},
}

# Configure task priorities (optional)
app.conf.task_default_priority = 5
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

# Configure result expiration
app.conf.result_expires = 3600  # Results expire after 1 hour

# Configure task time limits
app.conf.task_soft_time_limit = 300  # 5 minutes soft limit
app.conf.task_time_limit = 600  # 10 minutes hard limit

# Configure retry policy
app.conf.task_default_retry_delay = 60  # Retry after 60 seconds
app.conf.task_max_retries = 3


if __name__ == '__main__':
    app.start()