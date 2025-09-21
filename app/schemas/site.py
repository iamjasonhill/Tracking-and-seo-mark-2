from pydantic import BaseModel

class SiteBase(BaseModel):
    site_url: str
    enabled: bool = True

class SiteCreate(SiteBase):
    pass

class Site(SiteBase):
    id: int

    class Config:
        orm_mode = True
