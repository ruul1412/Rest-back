from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
from fastapi import Depends, HTTPException
from app.core.database import get_db

# ── Bcrypt ────────────────────────────────────────────────────────────────────
 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
 
def hash_password(password: str) -> str:
    return pwd_context.hash(password)
 
 
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

#  ── JWT ───────────────────────────────────────────────────────────────────────
 
def create_access_token(
    data: dict,
    expires_minutes: int | None = None,
    token_type: str = "access_token"
) -> str:
    to_encode = data.copy()

    duration = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES

    expire = datetime.now(timezone.utc) + timedelta(minutes=duration)

    to_encode.update({
        "exp": expire,
        "type": token_type
    })

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def decode_token(token: str, expected_type: str = "access_token") -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado"
        )

    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=401,
            detail="Tipo de token inválido"
        )

    return payload


def decode_access_token(token: str) -> dict:
    return decode_token(token, "access_token")


def decode_selection_token(token: str) -> dict:
    return decode_token(token, "branch_selection")
