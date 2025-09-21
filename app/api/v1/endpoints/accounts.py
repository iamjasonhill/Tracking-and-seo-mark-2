from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.schemas.account import Account, AccountCreate, AccountUpdate


router = APIRouter()


@router.post("/", response_model=Account, status_code=status.HTTP_201_CREATED)
def create_account(
    *, db: Session = Depends(deps.get_db), account_in: AccountCreate
) -> Account:
    owner = crud.user.get(db, user_id=account_in.user_id)
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return crud.account.create(db, obj_in=account_in)


@router.get("/", response_model=List[Account])
def read_accounts(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
) -> List[Account]:
    return crud.account.get_multi(db, skip=skip, limit=limit, user_id=user_id)


@router.get("/{account_id}", response_model=Account)
def read_account(*, db: Session = Depends(deps.get_db), account_id: int) -> Account:
    db_account = crud.account.get(db, account_id=account_id)
    if not db_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return db_account


@router.put("/{account_id}", response_model=Account)
def update_account(
    *,
    db: Session = Depends(deps.get_db),
    account_id: int,
    account_in: AccountUpdate,
) -> Account:
    db_account = crud.account.get(db, account_id=account_id)
    if not db_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return crud.account.update(db, db_obj=db_account, obj_in=account_in)


@router.delete("/{account_id}", response_model=Account)
def delete_account(*, db: Session = Depends(deps.get_db), account_id: int) -> Account:
    db_account = crud.account.get(db, account_id=account_id)
    if not db_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return crud.account.remove(db, db_obj=db_account)
