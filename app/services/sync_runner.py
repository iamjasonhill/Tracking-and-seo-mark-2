"""Utilities to orchestrate sync pipelines for provider integrations."""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.orm import Session

from app.models.site import Site

logger = logging.getLogger(__name__)


class SyncRunner:
    """High-level orchestration for running backfill and daily syncs.

    The concrete provider integrations will be implemented in follow-up issues.
    For now, the runner simply logs activity so Celery tasks have a stable
    integration point.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def run_backfill(self, site: Site) -> None:
        """Run a historical backfill for the given site."""
        logger.info("Starting backfill for site %s", site.site_url)

    def run_daily_sync(self, site: Site, *, run_date: date | None = None) -> None:
        """Run the daily incremental sync for the given site."""
        logger.info(
            "Running daily sync for site %s on %s",
            site.site_url,
            run_date or date.today(),
        )

