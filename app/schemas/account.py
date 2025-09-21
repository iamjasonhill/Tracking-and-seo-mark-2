from pydantic import BaseModel

class AccountBase(BaseModel):
    provider: str

class AccountCreate(AccountBase):
    credentials: dict

class Account(AccountBase):
    id: int

    class Config:
        orm_mode = True
