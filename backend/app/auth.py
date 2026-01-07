from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from . import crud
from .database import get_db
from .schemas import UserCreate, UserLogin, TokenResponse
from .utils.security import create_access_token, get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered."
        )
    hashed_password = get_password_hash(payload.password)
    user = crud.create_user(
        db,
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hashed_password,
        role=payload.role,
        company_name=payload.company_name,
    )
    token, expires_at = create_access_token(user_id=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        expires_at=expires_at,
        user=user,
    )


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, expires_at = create_access_token(user_id=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        expires_at=expires_at,
        user=user,
    )
