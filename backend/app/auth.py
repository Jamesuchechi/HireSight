from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from . import crud
from .database import get_db
from .schemas import (
    UserCreate, UserLogin, TokenResponse, EmailVerificationRequest,
    PasswordResetRequest, PasswordResetConfirm, UserOut
)
from .utils.security import create_access_token, get_password_hash, verify_password
from .config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Validate password length (argon2 can handle up to 128 bytes)
    if len(user_data.password.encode("utf-8")) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be 128 characters or less"
        )

    existing = crud.get_user_by_email(db, user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered."
        )

    # Create user (this also creates the profile)
    user = crud.create_user(db, user_data)

    # Create verification token
    expires_at = datetime.utcnow() + timedelta(hours=24)
    verification_token = crud.create_verification_token(db, user.id, expires_at)

    # TODO: Send verification email (implement background task)

    # For now, return success but don't give JWT until verified
    raise HTTPException(
        status_code=status.HTTP_201_CREATED,
        detail="Registration successful. Please check your email to verify your account."
    )


@router.post("/verify-email")
def verify_email(request: EmailVerificationRequest, db: Session = Depends(get_db)):
    token = crud.get_verification_token(db, request.token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token."
        )

    if token.expires_at < datetime.utcnow():
        crud.delete_verification_token(db, token.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired."
        )

    # Mark user as verified
    user = crud.update_user_verification(db, token.user_id, True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found."
        )

    # Delete the token
    crud.delete_verification_token(db, token.id)

    # Now create JWT tokens
    access_token, expires_at = create_access_token(user_id=user.id, account_type=user.account_type)

    # Create refresh token
    refresh_expires_at = datetime.utcnow() + timedelta(days=7)
    refresh_token = crud.create_refresh_token(db, user.id, refresh_expires_at)

    return TokenResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=user,
    )


@router.post("/login", response_model=TokenResponse)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, login_data.email)
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated."
        )

    # Create tokens
    access_token, expires_at = create_access_token(user_id=user.id, account_type=user.account_type)

    # Create refresh token
    refresh_expires_at = datetime.utcnow() + timedelta(days=7)
    refresh_token = crud.create_refresh_token(db, user.id, refresh_expires_at)

    return TokenResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=user,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(db: Session = Depends(get_db)):
    # TODO: Extract refresh token from httpOnly cookie
    # For now, this is a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token endpoint not implemented yet."
    )


@router.post("/logout")
def logout(db: Session = Depends(get_db)):
    # TODO: Extract refresh token from cookie and delete it
    # For now, this is a placeholder
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, request.email)
    # Always return success for security (don't reveal if email exists)

    if user:
        # Create password reset token
        expires_at = datetime.utcnow() + timedelta(hours=1)
        # TODO: Create reset token and send email

    return {"message": "If an account with that email exists, a password reset link has been sent."}


@router.post("/reset-password")
def reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    # TODO: Validate reset token
    # For now, this is a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not implemented yet."
    )


@router.get("/me", response_model=UserOut)
def get_current_user(db: Session = Depends(get_db)):
    # TODO: Implement JWT authentication dependency
    # For now, this is a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not implemented yet."
    )
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
