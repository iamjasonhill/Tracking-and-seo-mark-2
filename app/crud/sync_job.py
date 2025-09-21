from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.sync_job import SyncJob
from app.schemas.sync_job import SyncJobCreate, SyncJobUpdate


class CRUDSyncJob:
    def get(self, db: Session, sync_job_id: int) -> Optional[SyncJob]:
        return db.query(SyncJob).filter(SyncJob.id == sync_job_id).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        site_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[SyncJob]:
        query = db.query(SyncJob)
        if site_id is not None:
            query = query.filter(SyncJob.site_id == site_id)
        if status is not None:
            query = query.filter(SyncJob.status == status)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: SyncJobCreate) -> SyncJob:
        db_obj = SyncJob(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: SyncJob, obj_in: SyncJobUpdate) -> SyncJob:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, db_obj: SyncJob) -> SyncJob:
        db.delete(db_obj)
        db.commit()
        return db_obj


sync_job = CRUDSyncJob()
