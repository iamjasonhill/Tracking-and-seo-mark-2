from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.schemas.site import Site, SiteCreate, SiteUpdate


router = APIRouter()


@router.post("/", response_model=Site, status_code=status.HTTP_201_CREATED)
def create_site(*, db: Session = Depends(deps.get_db), site_in: SiteCreate) -> Site:
    account = crud.account.get(db, account_id=site_in.account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return crud.site.create(db, obj_in=site_in)


@router.get("/", response_model=List[Site])
def read_sites(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    account_id: Optional[int] = None,
    enabled: Optional[bool] = None,
) -> List[Site]:
    return crud.site.get_multi(
        db,
        skip=skip,
        limit=limit,
        account_id=account_id,
        enabled=enabled,
    )


@router.get("/{site_id}", response_model=Site)
def read_site(*, db: Session = Depends(deps.get_db), site_id: int) -> Site:
    db_site = crud.site.get(db, site_id=site_id)
    if not db_site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return db_site


@router.put("/{site_id}", response_model=Site)
def update_site(
    *,
    db: Session = Depends(deps.get_db),
    site_id: int,
    site_in: SiteUpdate,
) -> Site:
    db_site = crud.site.get(db, site_id=site_id)
    if not db_site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return crud.site.update(db, db_obj=db_site, obj_in=site_in)


@router.delete("/{site_id}", response_model=Site)
def delete_site(*, db: Session = Depends(deps.get_db), site_id: int) -> Site:
    db_site = crud.site.get(db, site_id=site_id)
    if not db_site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return crud.site.remove(db, db_obj=db_site)
