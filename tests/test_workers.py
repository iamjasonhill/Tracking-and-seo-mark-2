from __future__ import annotations

from uuid import uuid4

import pytest

from app.db.session import SessionLocal
from app.models.account import Account
from app.models.site import Site
from app.models.sync_job import SyncJob
from app.models.user import User
from workers.celery_app import celery_app, refresh_periodic_tasks
from workers.tasks import run_backfill, run_daily_sync


@pytest.fixture
def seeded_site(db_engine) -> Site:
    session = SessionLocal()
    try:
        user = User(email=f"worker-{uuid4()}@example.com", password_hash="hash")
        session.add(user)
        session.flush()

        account = Account(user_id=user.id, provider="google", credentials={"token": "x"})
        session.add(account)
        session.flush()

        site = Site(account_id=account.id, site_url="https://example.com", enabled=True)
        session.add(site)
        session.commit()
        session.refresh(site)
        return site
    finally:
        session.close()


def test_run_daily_sync_creates_successful_job(db_engine, seeded_site) -> None:
    result = run_daily_sync.apply(args=(seeded_site.id,))
    assert result.get() > 0

    session = SessionLocal()
    try:
        job = session.query(SyncJob).filter(SyncJob.site_id == seeded_site.id).one()
        assert job.status == "succeeded"
        assert job.finished_at is not None
    finally:
        session.close()


def test_run_backfill_creates_job_record(db_engine, seeded_site) -> None:
    result = run_backfill.apply(args=(seeded_site.id,))
    assert result.get() > 0

    session = SessionLocal()
    try:
        jobs = session.query(SyncJob).filter(SyncJob.site_id == seeded_site.id).all()
        assert any(job.status == "succeeded" for job in jobs)
    finally:
        session.close()


def test_run_daily_sync_failure_marks_job(monkeypatch, db_engine, seeded_site) -> None:
    from app.services import sync_runner as runner_module

    def fail(*_: object, **__: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(runner_module.SyncRunner, "run_daily_sync", fail)
    result = run_daily_sync.apply(args=(seeded_site.id,))
    with pytest.raises(RuntimeError):
        result.get()

    session = SessionLocal()
    try:
        job = session.query(SyncJob).filter(SyncJob.site_id == seeded_site.id).order_by(SyncJob.id.desc()).first()
        assert job is not None
        assert job.status == "failed"
        assert "boom" in (job.error or "")
    finally:
        session.close()


def test_refresh_periodic_tasks_builds_schedule(db_engine, seeded_site) -> None:
    schedule = refresh_periodic_tasks(celery_app)
    key = f"daily-sync-site-{seeded_site.id}"
    assert key in schedule
    assert schedule[key]["task"] == "workers.tasks.run_daily_sync"

    # Disable the site and ensure it is removed from the schedule
    session = SessionLocal()
    try:
        site = session.get(Site, seeded_site.id)
        assert site is not None
        site.enabled = False
        session.add(site)
        session.commit()
    finally:
        session.close()

    schedule = refresh_periodic_tasks(celery_app)
    assert key not in schedule
