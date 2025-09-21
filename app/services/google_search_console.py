"""Google Search Console integration helpers."""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from typing import Any, Callable, Iterable, Sequence

from googleapiclient.errors import HttpError

from app.services.types import SearchAnalyticsRow

logger = logging.getLogger(__name__)

RowList = list[SearchAnalyticsRow]


class GoogleSearchConsoleService:
    """Lightweight wrapper around the Search Console API."""

    _HISTORY_WINDOW_DAYS = 16 * 31  # ~16 months

    def __init__(
        self,
        credentials: dict[str, Any],
        *,
        client_factory: Callable[[], Any] | None = None,
        row_limit: int = 25_000,
    ) -> None:
        self.credentials = credentials
        self._client_factory = client_factory or self._default_client_factory
        self._client: Any | None = None
        self._row_limit = row_limit

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def fetch_backfill(self, site_url: str, *, end_date: date | None = None) -> RowList:
        """Fetch the historical backfill window for the provided site."""

        end = end_date or (date.today() - timedelta(days=1))
        start = end - timedelta(days=self._HISTORY_WINDOW_DAYS - 1)
        return self._fetch_range(site_url, start, end)

    def fetch_daily(self, site_url: str, run_date: date) -> RowList:
        """Fetch analytics for a specific date."""

        return self._fetch_range(site_url, run_date, run_date)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _default_client_factory(self) -> Any:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        if "token" in self.credentials and "refresh_token" not in self.credentials:
            # Support simple API key style credentials for testing environments.
            return build(
                "searchconsole",
                "v1",
                developerKey=self.credentials["token"],
                cache_discovery=False,
            )

        creds = Credentials.from_authorized_user_info(self.credentials)
        return build("searchconsole", "v1", credentials=creds, cache_discovery=False)

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = self._client_factory()
        return self._client

    def _fetch_range(self, site_url: str, start: date, end: date) -> RowList:
        rows: RowList = []
        for dimension in ("query", "page"):
            rows.extend(self._fetch_dimension(site_url, start, end, dimension))
        return rows

    def _fetch_dimension(
        self, site_url: str, start: date, end: date, dimension: str
    ) -> RowList:
        start_row = 0
        collected: RowList = []
        while True:
            body = {
                "startDate": start.isoformat(),
                "endDate": end.isoformat(),
                "dimensions": ["date", dimension],
                "rowLimit": self._row_limit,
                "startRow": start_row,
            }
            logger.debug(
                "Querying GSC for %s [%s - %s] dimension=%s startRow=%s",
                site_url,
                body["startDate"],
                body["endDate"],
                dimension,
                start_row,
            )
            response = self._execute_with_retry(site_url, body)
            batch = self._convert_rows(response.get("rows", []), dimension)
            collected.extend(batch)
            if len(batch) < self._row_limit:
                break
            start_row += len(batch)
        return collected

    def _execute_with_retry(self, site_url: str, body: dict[str, Any]) -> dict[str, Any]:
        attempt = 0
        delay = 0.1
        last_error: Exception | None = None
        while attempt < 3:
            try:
                client = self._get_client()
                query = client.searchanalytics().query(siteUrl=site_url, body=body)
                return query.execute()
            except HttpError as exc:  # pragma: no cover - exercised via retry logic
                last_error = exc
                status = getattr(exc.resp, "status", "unknown")
                logger.error(
                    "GSC request failed",
                    extra={
                        "site": site_url,
                        "status": status,
                        "body": getattr(exc, "content", b"").decode(errors="ignore"),
                        "attempt": attempt + 1,
                    },
                )
                attempt += 1
                if attempt >= 3:
                    raise
                time.sleep(delay)
                delay *= 2
        if last_error:
            raise last_error
        return {}

    @staticmethod
    def _convert_rows(rows: Iterable[dict[str, Any]], dimension: str) -> RowList:
        normalized: RowList = []
        for row in rows:
            keys: Sequence[str] = row.get("keys", [])
            if len(keys) < 2:
                continue
            try:
                row_date = date.fromisoformat(keys[0])
            except ValueError:
                logger.debug("Skipping row with invalid date: %s", keys)
                continue
            normalized.append(
                SearchAnalyticsRow(
                    date=row_date,
                    dimension=dimension,
                    key=keys[1],
                    clicks=int(row.get("clicks", 0)),
                    impressions=int(row.get("impressions", 0)),
                    ctr=float(row.get("ctr", 0.0)),
                    position=float(row.get("position", 0.0)),
                )
            )
        return normalized

    def close(self) -> None:
        client = self._client
        if client is not None:
            try:
                close = getattr(client, "close", None)
                if callable(close):
                    close()
            finally:
                self._client = None


__all__ = ["GoogleSearchConsoleService"]
