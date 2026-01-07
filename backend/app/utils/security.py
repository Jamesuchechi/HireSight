from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..config import settings
from .. import crud, models
from ..database import get_db
from ..schemas import TokenPayload, AccountType

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
MAX_PASSWORD_BYTES = 128  # Argon2 can handle longer passwords
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_password_hash(password: str) -> str:
    normalized = normalize_password(password)
    return pwd_context.hash(normalized)


def normalize_password(password: str) -> str:
    """Normalize password by truncating to maximum safe length."""
    if len(password.encode("utf-8")) <= MAX_PASSWORD_BYTES:
        return password
    # Truncate to byte limit and decode back
    truncated_bytes = password.encode("utf-8")[:MAX_PASSWORD_BYTES]
    return truncated_bytes.decode("utf-8", errors="ignore")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(normalize_password(plain_password), hashed_password)


def create_access_token(user_id: str, account_type: str) -> tuple[str, datetime]:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "account_type": account_type,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expire


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")
        account_type_value: str | None = payload.get("account_type")
        exp_value = payload.get("exp")
        if user_id is None or account_type_value is None or exp_value is None:
            raise credentials_exception
        token_data = TokenPayload(
            sub=user_id,
            account_type=AccountType(account_type_value),
            exp=datetime.utcfromtimestamp(exp_value),
        )
    except (JWTError, ValueError):
        raise credentials_exception
    user = crud.get_user_by_id(db, user_id=token_data.sub)
    if not user:
        raise credentials_exception
    return user


def get_current_verified_user(user: Annotated[models.User, Depends(get_current_user)]) -> models.User:
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Email verification required"
        )
    return user


def get_current_personal_user(user: Annotated[models.User, Depends(get_current_verified_user)]) -> models.User:
    if user.account_type != "personal":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Personal account required to perform this action",
        )
    return user


def get_current_company_user(user: Annotated[models.User, Depends(get_current_verified_user)]) -> models.User:
    if user.account_type != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company account required to perform this action",
        )
    return user
