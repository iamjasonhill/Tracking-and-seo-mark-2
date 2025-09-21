from typing import Optional

from pydantic import BaseModel, ConfigDict


class SiteBase(BaseModel):
    site_url: str
    enabled: bool = True


class SiteCreate(SiteBase):
    account_id: int


class SiteUpdate(BaseModel):
    site_url: Optional[str] = None
    enabled: Optional[bool] = None


class Site(SiteBase):
    id: int
    account_id: int

    model_config = ConfigDict(from_attributes=True)
