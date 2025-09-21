from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate


class CRUDAccount:
    def get(self, db: Session, account_id: int) -> Optional[Account]:
        return db.query(Account).filter(Account.id == account_id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, user_id: Optional[int] = None
    ) -> List[Account]:
        query = db.query(Account)
        if user_id is not None:
            query = query.filter(Account.user_id == user_id)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: AccountCreate) -> Account:
        db_obj = Account(
            user_id=obj_in.user_id,
            provider=obj_in.provider,
            credentials=obj_in.credentials,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Account, obj_in: AccountUpdate) -> Account:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, db_obj: Account) -> Account:
        db.delete(db_obj)
        db.commit()
        return db_obj


account = CRUDAccount()
