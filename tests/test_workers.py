from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.db.session import SessionLocal
from app.models.account import Account
from app.models.search_data import SearchData
from app.models.site import Site
from app.models.sync_job import SyncJob
from app.models.user import User
from app.services.types import SearchAnalyticsRow
from workers.celery_app import celery_app, refresh_periodic_tasks
from workers.tasks import run_backfill, run_daily_sync


@pytest.fixture(autouse=True)
def mock_provider_services(monkeypatch):
    class DummyGoogleService:
        def __init__(self, _: dict[str, object]) -> None:
            self.calls: list[str] = []

        def fetch_daily(self, site_url: str, run_date: date) -> list[SearchAnalyticsRow]:
            self.calls.append("daily")
            return [
                SearchAnalyticsRow(
                    date=run_date,
                    dimension="query",
                    key=f"kw-{site_url}",
                    clicks=5,
                    impressions=10,
                    ctr=0.5,
                    position=3.2,
                ),
                SearchAnalyticsRow(
                    date=run_date,
                    dimension="page",
                    key=f"{site_url}/page",
                    clicks=2,
                    impressions=4,
                    ctr=0.5,
                    position=5.0,
                ),
            ]

        def fetch_backfill(self, site_url: str) -> list[SearchAnalyticsRow]:
            today = date.today()
            return [
                SearchAnalyticsRow(
                    date=today - timedelta(days=2),
                    dimension="query",
                    key=f"kw-{site_url}",
                    clicks=7,
                    impressions=20,
                    ctr=0.35,
                    position=4.2,
                ),
                SearchAnalyticsRow(
                    date=today - timedelta(days=1),
                    dimension="page",
                    key=f"{site_url}/other",
                    clicks=1,
                    impressions=3,
                    ctr=0.33,
                    position=6.0,
                ),
            ]

        def close(self) -> None:  # pragma: no cover - compatibility shim
            return None

    class DummyBingService(DummyGoogleService):
        pass

    monkeypatch.setattr(
        "app.services.sync_runner.GoogleSearchConsoleService",
        DummyGoogleService,
    )
    monkeypatch.setattr(
        "app.services.sync_runner.BingWebmasterService",
        DummyBingService,
    )


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
        rows = (
            session.query(SearchData)
            .filter(SearchData.site_id == seeded_site.id)
            .order_by(SearchData.date.asc())
            .all()
        )
        assert rows
        assert {row.dimension for row in rows} == {"query", "page"}
    finally:
        session.close()


def test_run_backfill_creates_job_record(db_engine, seeded_site) -> None:
    result = run_backfill.apply(args=(seeded_site.id,))
    assert result.get() > 0

    session = SessionLocal()
    try:
        jobs = session.query(SyncJob).filter(SyncJob.site_id == seeded_site.id).all()
        assert any(job.status == "succeeded" for job in jobs)
        rows = (
            session.query(SearchData)
            .filter(SearchData.site_id == seeded_site.id)
            .order_by(SearchData.date.asc())
            .all()
        )
        assert rows
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
