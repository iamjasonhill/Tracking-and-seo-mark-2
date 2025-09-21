from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.schemas.sync_job import SyncJob, SyncJobCreate, SyncJobUpdate


router = APIRouter()


@router.post("/", response_model=SyncJob, status_code=status.HTTP_201_CREATED)
def create_sync_job(
    *, db: Session = Depends(deps.get_db), sync_job_in: SyncJobCreate
) -> SyncJob:
    site = crud.site.get(db, site_id=sync_job_in.site_id)
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return crud.sync_job.create(db, obj_in=sync_job_in)


@router.get("/", response_model=List[SyncJob])
def read_sync_jobs(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    site_id: Optional[int] = None,
    status_filter: Optional[str] = None,
) -> List[SyncJob]:
    return crud.sync_job.get_multi(
        db,
        skip=skip,
        limit=limit,
        site_id=site_id,
        status=status_filter,
    )


@router.get("/{sync_job_id}", response_model=SyncJob)
def read_sync_job(*, db: Session = Depends(deps.get_db), sync_job_id: int) -> SyncJob:
    db_sync_job = crud.sync_job.get(db, sync_job_id=sync_job_id)
    if not db_sync_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sync job not found")
    return db_sync_job


@router.put("/{sync_job_id}", response_model=SyncJob)
def update_sync_job(
    *,
    db: Session = Depends(deps.get_db),
    sync_job_id: int,
    sync_job_in: SyncJobUpdate,
) -> SyncJob:
    db_sync_job = crud.sync_job.get(db, sync_job_id=sync_job_id)
    if not db_sync_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sync job not found")
    return crud.sync_job.update(db, db_obj=db_sync_job, obj_in=sync_job_in)


@router.delete("/{sync_job_id}", response_model=SyncJob)
def delete_sync_job(*, db: Session = Depends(deps.get_db), sync_job_id: int) -> SyncJob:
    db_sync_job = crud.sync_job.get(db, sync_job_id=sync_job_id)
    if not db_sync_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sync job not found")
    return crud.sync_job.remove(db, db_obj=db_sync_job)
