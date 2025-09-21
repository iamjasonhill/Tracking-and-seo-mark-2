from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SyncJobBase(BaseModel):
    site_id: int
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None


class SyncJobCreate(SyncJobBase):
    pass


class SyncJobUpdate(BaseModel):
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None


class SyncJob(SyncJobBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
