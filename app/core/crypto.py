"""Helpers for encrypting and decrypting sensitive payloads."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Mapping

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class CredentialEncryptionError(RuntimeError):
    """Raised when encrypted credentials cannot be decrypted."""


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    """Return a cached ``Fernet`` instance using the configured key."""

    key = settings.ENCRYPTION_KEY
    if not key:
        raise RuntimeError("ENCRYPTION_KEY must be configured")
    if isinstance(key, str):
        key_bytes = key.encode("utf-8")
    else:
        key_bytes = key
    return Fernet(key_bytes)


def encrypt_dict(payload: Mapping[str, Any]) -> str:
    """Encrypt a dictionary payload using the configured Fernet key."""

    serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    token = _get_fernet().encrypt(serialized.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_dict(token: str) -> dict[str, Any]:
    """Decrypt a previously encrypted payload into its dictionary form."""

    try:
        decrypted = _get_fernet().decrypt(token.encode("utf-8"))
    except InvalidToken as exc:  # pragma: no cover - defensive guard
        raise CredentialEncryptionError("Invalid credentials payload") from exc
    return json.loads(decrypted.decode("utf-8"))


__all__ = ["CredentialEncryptionError", "decrypt_dict", "encrypt_dict"]
