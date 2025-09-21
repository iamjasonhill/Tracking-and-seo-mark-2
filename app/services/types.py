"""Shared types for search provider ingestion services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class SearchAnalyticsRow:
    """Represents a single analytics record returned by a provider API."""

    date: date
    dimension: str
    key: str
    clicks: int
    impressions: int
    ctr: float
    position: float
