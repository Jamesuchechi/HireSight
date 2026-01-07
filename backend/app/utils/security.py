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
from ..schemas import TokenPayload, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_BCRYPT_PASSWORD_BYTES = 72
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_password_hash(password: str) -> str:
    normalized = normalize_password(password)
    return pwd_context.hash(normalized)


def normalize_password(password: str) -> str:
    encoded = password.encode("utf-8", errors="ignore")
    if len(encoded) <= MAX_BCRYPT_PASSWORD_BYTES:
        return password
    truncated = encoded[:MAX_BCRYPT_PASSWORD_BYTES]
    return truncated.decode("utf-8", errors="ignore")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(normalize_password(plain_password), hashed_password)


def create_access_token(user_id: str, role: UserRole) -> tuple[str, datetime]:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role.value,
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
        role_value: str | None = payload.get("role")
        exp_value = payload.get("exp")
        if user_id is None or role_value is None or exp_value is None:
            raise credentials_exception
        token_data = TokenPayload(
            sub=user_id,
            role=UserRole(role_value),
            exp=datetime.utcfromtimestamp(exp_value),
        )
    except (JWTError, ValueError):
        raise credentials_exception
    user = crud.get_user_by_id(db, user_id=token_data.sub)
    if not user:
        raise credentials_exception
    return user


def get_current_active_user(user: Annotated[models.User, Depends(get_current_user)]) -> models.User:
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return user


def get_current_company_user(user: Annotated[models.User, Depends(get_current_active_user)]) -> models.User:
    if user.role != UserRole.company:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company access required to perform this action",
        )
    return user
