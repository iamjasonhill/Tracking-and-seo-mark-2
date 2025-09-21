from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.providers import normalize_provider


class AccountBase(BaseModel):
    provider: str

    @field_validator("provider")
    @classmethod
    def _normalize_provider(cls, value: str) -> str:
        return normalize_provider(value)


class AccountCreate(AccountBase):
    credentials: dict[str, Any]
    user_id: int


class AccountUpdate(BaseModel):
    provider: Optional[str] = None
    credentials: Optional[dict[str, Any]] = None

    @field_validator("provider")
    @classmethod
    def _normalize_optional_provider(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return normalize_provider(value)


class Account(AccountBase):
    id: int
    user_id: int
    credentials: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
