"""Bing Webmaster Tools integration helpers."""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from typing import Any, Iterable

import httpx

from app.services.types import SearchAnalyticsRow

logger = logging.getLogger(__name__)

RowList = list[SearchAnalyticsRow]


class BingWebmasterService:
    """Wrapper for Bing Webmaster Tools analytics endpoints."""

    _BASE_URL = "https://api.bing.microsoft.com/v7.0/Webmaster"
    _HISTORY_WINDOW_DAYS = 365

    def __init__(
        self,
        credentials: dict[str, Any],
        *,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        api_key = credentials.get("api_key") or credentials.get("key") or credentials.get("token")
        if not api_key:
            raise ValueError("Bing credentials must include an API key")
        self._api_key = api_key
        self._client = client or httpx.Client(timeout=timeout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def fetch_backfill(self, site_url: str, *, end_date: date | None = None) -> RowList:
        end = end_date or (date.today() - timedelta(days=1))
        start = end - timedelta(days=self._HISTORY_WINDOW_DAYS - 1)
        return self._fetch_range(site_url, start, end)

    def fetch_daily(self, site_url: str, run_date: date) -> RowList:
        return self._fetch_range(site_url, run_date, run_date)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _fetch_range(self, site_url: str, start: date, end: date) -> RowList:
        query_rows = self._request_with_retry("/QueryStats", site_url, start, end)
        page_rows = self._request_with_retry("/PageStats", site_url, start, end)
        rows: RowList = []
        rows.extend(self._normalize(query_rows, dimension="query"))
        rows.extend(self._normalize(page_rows, dimension="page"))
        return rows

    def _request_with_retry(
        self, endpoint: str, site_url: str, start: date, end: date
    ) -> dict[str, Any]:
        attempt = 0
        delay = 0.1
        last_error: Exception | None = None
        params = {
            "siteUrl": site_url,
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
        }
        headers = {"Ocp-Apim-Subscription-Key": self._api_key}
        while attempt < 3:
            try:
                response = self._client.get(
                    f"{self._BASE_URL}{endpoint}",
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:  # pragma: no cover - retried in tests
                last_error = exc
                logger.error(
                    "Bing request failed",
                    extra={
                        "site": site_url,
                        "status": exc.response.status_code,
                        "body": exc.response.text,
                        "attempt": attempt + 1,
                        "endpoint": endpoint,
                    },
                )
                attempt += 1
                if attempt >= 3:
                    raise
                time.sleep(delay)
                delay *= 2
            except httpx.RequestError as exc:
                last_error = exc
                logger.error(
                    "Bing transport error",
                    extra={
                        "site": site_url,
                        "body": str(exc),
                        "attempt": attempt + 1,
                        "endpoint": endpoint,
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

    def _normalize(self, payload: dict[str, Any], *, dimension: str) -> RowList:
        rows: RowList = []
        items: Iterable[dict[str, Any]] = []
        if isinstance(payload, dict):
            if "value" in payload and isinstance(payload["value"], list):
                items = payload["value"]
            elif "d" in payload and isinstance(payload["d"], dict) and isinstance(
                payload["d"].get("results"), list
            ):
                items = payload["d"]["results"]
            elif dimension == "query" and isinstance(payload.get("queries"), list):
                items = payload["queries"]
            elif dimension == "page" and isinstance(payload.get("pages"), list):
                items = payload["pages"]

        for item in items:
            date_str = (
                item.get("date")
                or item.get("Date")
                or item.get("day")
                or item.get("Day")
            )
            if not date_str:
                continue
            try:
                row_date = date.fromisoformat(date_str[:10])
            except ValueError:
                logger.debug("Skipping Bing row with invalid date: %s", item)
                continue
            key = (
                item.get("query")
                or item.get("Query")
                or item.get("page")
                or item.get("Page")
                or ""
            )
            rows.append(
                SearchAnalyticsRow(
                    date=row_date,
                    dimension=dimension,
                    key=key,
                    clicks=int(item.get("clicks") or item.get("Clicks") or 0),
                    impressions=int(item.get("impressions") or item.get("Impressions") or 0),
                    ctr=float(item.get("ctr") or item.get("Ctr") or 0.0),
                    position=float(item.get("position") or item.get("Position") or 0.0),
                )
            )
        return rows

    def close(self) -> None:
        self._client.close()


__all__ = ["BingWebmasterService"]
