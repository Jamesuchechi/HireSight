from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from . import crud, models
from .database import get_db
from .schemas import (
    UserCreate, UserLogin, TokenResponse, EmailVerificationRequest,
    PasswordResetRequest, PasswordResetConfirm, UserOut
)
from .utils.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user
)
from .config import settings
from .services.email import send_verification_email, send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _attach_refresh_cookie(response: Response, token_value: str) -> None:
    """Attach an httpOnly refresh token cookie to the response."""
    response.set_cookie(
        settings.REFRESH_TOKEN_COOKIE_NAME,
        token_value,
        httponly=True,
        secure=settings.REFRESH_TOKEN_COOKIE_SECURE,
        samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
        path=settings.REFRESH_TOKEN_COOKIE_PATH,
        max_age=settings.REFRESH_TOKEN_COOKIE_MAX_AGE,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Remove the refresh token cookie."""
    response.delete_cookie(settings.REFRESH_TOKEN_COOKIE_NAME, path=settings.REFRESH_TOKEN_COOKIE_PATH)


def _get_user_display_name(user: models.User) -> str:
    if user.personal_profile and user.personal_profile.full_name:
        return user.personal_profile.full_name
    if user.company_profile and user.company_profile.company_name:
        return user.company_profile.company_name
    return user.email


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    # Validate password length (argon2 can handle up to 128 bytes)
    if len(user_data.password.encode("utf-8")) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be 128 characters or less"
        )

    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = registration_rate_limiter.allow_request(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
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
    background_tasks.add_task(
        send_verification_email,
        user.email,
        verification_token.token,
        user_data.name,
    )

    return {"message": "Registration successful. Please check your email to verify your account."}


@router.post("/verify-email", response_model=TokenResponse)
def verify_email(
    request: EmailVerificationRequest,
    response: Response,
    db: Session = Depends(get_db),
):
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
    refresh_expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = crud.create_refresh_token(db, user.id, refresh_expires_at)
    _attach_refresh_cookie(response, refresh_token.token)

    return TokenResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=user,
    )


@router.post("/login", response_model=TokenResponse)
def login_user(
    login_data: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_email(db, login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked until {user.locked_until.isoformat()}",
        )

    if not verify_password(login_data.password, user.password_hash):
        crud.record_failed_login_attempt(db, user)
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

    crud.reset_failed_login_attempts(db, user)

    access_token, expires_at = create_access_token(user_id=user.id, account_type=user.account_type)

    refresh_expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = crud.create_refresh_token(db, user.id, refresh_expires_at)
    _attach_refresh_cookie(response, refresh_token.token)

    return TokenResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=user,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    token_value = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if not token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing."
        )

    stored = crud.get_refresh_token(db, token_value)
    if not stored or stored.expires_at < datetime.utcnow():
        if stored:
            crud.delete_refresh_token(db, stored.token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or expired."
        )

    user = crud.get_user_by_id(db, stored.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found or inactive."
        )

    access_token, expires_at = create_access_token(user_id=user.id, account_type=user.account_type)

    crud.delete_refresh_token(db, stored.token)
    refresh_expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh = crud.create_refresh_token(db, user.id, refresh_expires_at)
    _attach_refresh_cookie(response, new_refresh.token)

    return TokenResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=user,
    )


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    token_value = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if token_value:
        crud.delete_refresh_token(db, token_value)
    _clear_refresh_cookie(response)
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
def forgot_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_email(db, request.email)
    # Always return success for security (don't reveal if email exists)

    if user:
        expires_at = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
        reset_token = crud.create_password_reset_token(db, user.id, expires_at)
        background_tasks.add_task(
            send_password_reset_email,
            user.email,
            reset_token.token,
            _get_user_display_name(user),
        )

    return {"message": "If an account with that email exists, a password reset link has been sent."}


@router.post("/reset-password")
def reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    reset_token = crud.get_password_reset_token(db, request.token)
    if not reset_token or reset_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token."
        )

    user = crud.get_user_by_id(db, reset_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found."
        )

    user.password_hash = get_password_hash(request.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    crud.delete_password_reset_token(db, reset_token.id)
    return {"message": "Password reset successfully."}


@router.get("/me", response_model=UserOut)
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return current_user
