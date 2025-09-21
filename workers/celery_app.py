"""Celery application and periodic schedule configuration."""

from __future__ import annotations

from typing import Dict

from celery import Celery
from celery.schedules import crontab
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.site import Site

celery_app = Celery("seo_sync")
celery_app.conf.broker_url = settings.CELERY_BROKER_URL
celery_app.conf.result_backend = settings.CELERY_RESULT_BACKEND
celery_app.conf.task_default_queue = "seo-sync"
celery_app.conf.timezone = settings.CELERY_TIMEZONE
celery_app.conf.beat_schedule = {}
celery_app.autodiscover_tasks(["workers"])


def _enabled_sites(session: Session) -> list[Site]:
    return session.query(Site).filter(Site.enabled.is_(True)).all()


def refresh_periodic_tasks(app: Celery = celery_app) -> Dict[str, dict]:
    """Rebuild the Celery beat schedule from the current site list."""
    schedule: Dict[str, dict] = {}
    session = SessionLocal()
    try:
        for site in _enabled_sites(session):
            schedule[f"daily-sync-site-{site.id}"] = {
                "task": "workers.tasks.run_daily_sync",
                "schedule": crontab(
                    hour=settings.DAILY_SYNC_HOUR,
                    minute=settings.DAILY_SYNC_MINUTE,
                ),
                "args": (site.id,),
            }
    finally:
        session.close()

    app.conf.beat_schedule = schedule
    return schedule


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **_: object) -> None:
    refresh_periodic_tasks(sender)


__all__ = ["celery_app", "refresh_periodic_tasks"]
