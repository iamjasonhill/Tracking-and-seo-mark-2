from typing import Optional

from pydantic import BaseModel


class AccountBase(BaseModel):
    provider: str


class AccountCreate(AccountBase):
    credentials: dict
    user_id: int


class AccountUpdate(BaseModel):
    provider: Optional[str] = None
    credentials: Optional[dict] = None


class Account(AccountBase):
    id: int
    user_id: int
    credentials: dict

    class Config:
        orm_mode = True
