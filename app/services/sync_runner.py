"""Utilities to orchestrate sync pipelines for provider integrations."""

from __future__ import annotations

import logging
from contextlib import suppress
from datetime import date, timedelta
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.search_data import SearchData
from app.models.site import Site

from .bing_webmaster import BingWebmasterService
from .google_search_console import GoogleSearchConsoleService
from .types import SearchAnalyticsRow

logger = logging.getLogger(__name__)

_PROVIDER_GOOGLE = "google"
_PROVIDER_BING = "bing"


class SyncRunner:
    """High-level orchestration for running backfill and daily syncs."""

    def __init__(
        self,
        db: Session,
        *,
        google_service_factory: type[GoogleSearchConsoleService] | None = None,
        bing_service_factory: type[BingWebmasterService] | None = None,
    ) -> None:
        self.db = db
        self._google_service_factory = google_service_factory or GoogleSearchConsoleService
        self._bing_service_factory = bing_service_factory or BingWebmasterService

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------
    def run_backfill(self, site: Site) -> int:
        """Run a historical backfill for the given site."""

        logger.info("Starting backfill for site %s", site.site_url)
        rows = self._collect_rows(site, mode="backfill")
        ingested = self._ingest(site, rows)
        logger.info("Backfill complete for %s (rows=%s)", site.site_url, ingested)
        return ingested

    def run_daily_sync(self, site: Site, *, run_date: date | None = None) -> int:
        """Run the daily incremental sync for the given site."""

        sync_date = run_date or (date.today() - timedelta(days=1))
        logger.info("Running daily sync for site %s on %s", site.site_url, sync_date)
        rows = self._collect_rows(site, mode="daily", run_date=sync_date)
        ingested = self._ingest(site, rows)
        logger.info(
            "Daily sync complete for %s on %s (rows=%s)", site.site_url, sync_date, ingested
        )
        return ingested

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _collect_rows(
        self,
        site: Site,
        *,
        mode: str,
        run_date: date | None = None,
    ) -> list[SearchAnalyticsRow]:
        account = site.account
        if account is None:
            raise ValueError("Site does not have an associated account")
        provider = (account.provider or "").lower()
        credentials = account.credentials or {}

        if provider == _PROVIDER_GOOGLE:
            service = self._google_service_factory(credentials)
        elif provider == _PROVIDER_BING:
            service = self._bing_service_factory(credentials)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        try:
            if mode == "daily":
                assert run_date is not None
                return service.fetch_daily(site.site_url, run_date)
            return service.fetch_backfill(site.site_url)
        finally:
            close = getattr(service, "close", None)
            if callable(close):  # pragma: no branch - defensive guard
                with suppress(Exception):
                    close()

    def _ingest(self, site: Site, rows: Iterable[SearchAnalyticsRow]) -> int:
        total = 0
        for row in rows:
            self._upsert_row(site, row)
            total += 1
        return total

    def _upsert_row(self, site: Site, row: SearchAnalyticsRow) -> None:
        stmt = select(SearchData).where(
            SearchData.site_id == site.id,
            SearchData.provider == site.account.provider,
            SearchData.date == row.date,
            SearchData.dimension == row.dimension,
            SearchData.key == row.key,
        )
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing:
            existing.clicks = row.clicks
            existing.impressions = row.impressions
            existing.ctr = row.ctr
            existing.position = row.position
        else:
            record = SearchData(
                site_id=site.id,
                provider=site.account.provider,
                date=row.date,
                dimension=row.dimension,
                key=row.key,
                clicks=row.clicks,
                impressions=row.impressions,
                ctr=row.ctr,
                position=row.position,
            )
            self.db.add(record)


__all__ = ["SyncRunner"]
