"""Celery worker package for the SEO data sync platform."""

from .celery_app import celery_app

__all__ = ["celery_app"]
