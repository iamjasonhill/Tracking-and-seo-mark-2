from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.schemas.user import User, UserCreate, UserUpdate


router = APIRouter()


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(*, db: Session = Depends(deps.get_db), user_in: UserCreate) -> User:
    existing_user = crud.user.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    return crud.user.create(db, obj_in=user_in)


@router.get("/", response_model=List[User])
def read_users(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> List[User]:
    return crud.user.get_multi(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=User)
def read_user(*, db: Session = Depends(deps.get_db), user_id: int) -> User:
    db_user = crud.user.get(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=User)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: UserUpdate,
) -> User:
    db_user = crud.user.get(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_in.email and user_in.email != db_user.email:
        existing_user = crud.user.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    return crud.user.update(db, db_obj=db_user, obj_in=user_in)


@router.delete("/{user_id}", response_model=User)
def delete_user(*, db: Session = Depends(deps.get_db), user_id: int) -> User:
    db_user = crud.user.get(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return crud.user.remove(db, db_obj=db_user)
