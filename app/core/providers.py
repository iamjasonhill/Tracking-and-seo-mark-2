"""Shared helpers for working with supported search providers."""

from __future__ import annotations

from typing import FrozenSet

SUPPORTED_PROVIDERS: FrozenSet[str] = frozenset({"google", "bing"})


def normalize_provider(value: str) -> str:
    """Normalize a provider identifier and ensure it is supported."""

    normalized = (value or "").strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        allowed = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise ValueError(f"Unsupported provider '{value}'. Expected one of: {allowed}.")
    return normalized


__all__ = ["SUPPORTED_PROVIDERS", "normalize_provider"]
