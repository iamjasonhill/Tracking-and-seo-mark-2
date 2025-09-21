from typing import Optional

from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class User(UserBase):
    id: int

    class Config:
        orm_mode = True
