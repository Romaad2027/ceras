from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from .config import get_settings


                                                                                            
                                                                                        
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Return a secure hash for the given plain-text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that the plain-text password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str | uuid.UUID,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token for the given subject (user id)."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
