"""
HireSight Django project initialization.

This module ensures that the Celery app is available when Django starts.
"""
from .celery import app as celery_app

__all__ = ['celery_app']