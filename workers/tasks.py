"""Celery tasks that drive historical backfills and daily syncs."""

from __future__ import annotations

from datetime import datetime, timezone

from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session

from app.crud.sync_job import sync_job as sync_job_crud
from app.db.session import SessionLocal
from app.models.site import Site
from app.schemas.sync_job import SyncJobCreate, SyncJobUpdate
from app.services.sync_runner import SyncRunner

from .celery_app import celery_app

logger = get_task_logger(__name__)


def _load_site(session: Session, site_id: int) -> Site:
    site = session.query(Site).filter(Site.id == site_id).first()
    if site is None:
        raise ValueError(f"Site {site_id} does not exist")
    if not site.enabled:
        raise ValueError(f"Site {site_id} is disabled")
    return site


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _create_sync_job(session: Session, site_id: int) -> int:
    job = sync_job_crud.create(
        session,
        obj_in=SyncJobCreate(
            site_id=site_id,
            status="running",
            started_at=_utcnow(),
        ),
    )
    return job.id


def _mark_job_succeeded(session: Session, job_id: int) -> None:
    job = sync_job_crud.get(session, job_id)
    if job is None:
        return
    sync_job_crud.update(
        session,
        db_obj=job,
        obj_in=SyncJobUpdate(
            status="succeeded",
            finished_at=_utcnow(),
            error=None,
        ),
    )


def _mark_job_failed(job_id: int | None, *, site_id: int, error: Exception) -> None:
    error_message = str(error)
    session = SessionLocal()
    try:
        if job_id is None:
            sync_job_crud.create(
                session,
                obj_in=SyncJobCreate(
                    site_id=site_id,
                    status="failed",
                    started_at=_utcnow(),
                    finished_at=_utcnow(),
                    error=error_message,
                ),
            )
        else:
            job = sync_job_crud.get(session, job_id)
            if job is None:
                return
            sync_job_crud.update(
                session,
                db_obj=job,
                obj_in=SyncJobUpdate(
                    status="failed",
                    finished_at=_utcnow(),
                    error=error_message,
                ),
            )
    finally:
        session.close()


def _run_with_job(site_id: int, runner_fn: str) -> int:
    session = SessionLocal()
    job_id: int | None = None
    try:
        site = _load_site(session, site_id)
        job_id = _create_sync_job(session, site_id)
        runner = SyncRunner(session)
        if runner_fn == "backfill":
            runner.run_backfill(site)
        else:
            runner.run_daily_sync(site)
        session.commit()
        _mark_job_succeeded(session, job_id)
        return job_id
    except Exception as exc:  # noqa: BLE001 - propagate task failure after logging
        session.rollback()
        _mark_job_failed(job_id, site_id=site_id, error=exc)
        logger.exception("%s task failed for site %s", runner_fn, site_id)
        raise
    finally:
        session.close()


@celery_app.task(name="workers.tasks.run_backfill")
def run_backfill(site_id: int) -> int:
    """Kick off a historical backfill for the provided site."""
    return _run_with_job(site_id, "backfill")


@celery_app.task(name="workers.tasks.run_daily_sync")
def run_daily_sync(site_id: int) -> int:
    """Run the daily incremental sync for the provided site."""
    return _run_with_job(site_id, "daily")


__all__ = ["run_backfill", "run_daily_sync"]
