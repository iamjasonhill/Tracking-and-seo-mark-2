from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.site import Site
from app.schemas.site import SiteCreate, SiteUpdate


class CRUDSite:
    def get(self, db: Session, site_id: int) -> Optional[Site]:
        return db.query(Site).filter(Site.id == site_id).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        account_id: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> List[Site]:
        query = db.query(Site)
        if account_id is not None:
            query = query.filter(Site.account_id == account_id)
        if enabled is not None:
            query = query.filter(Site.enabled == enabled)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: SiteCreate) -> Site:
        db_obj = Site(
            account_id=obj_in.account_id,
            site_url=obj_in.site_url,
            enabled=obj_in.enabled,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Site, obj_in: SiteUpdate) -> Site:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, db_obj: Site) -> Site:
        db.delete(db_obj)
        db.commit()
        return db_obj


site = CRUDSite()
