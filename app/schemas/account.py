from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AccountBase(BaseModel):
    provider: str


class AccountCreate(AccountBase):
    credentials: dict[str, Any]
    user_id: int


class AccountUpdate(BaseModel):
    provider: Optional[str] = None
    credentials: Optional[dict[str, Any]] = None


class Account(AccountBase):
    id: int
    user_id: int
    credentials: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
