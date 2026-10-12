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
 
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire, "type": "access_token"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
 
 
def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
 
    if payload.get("type") != "access_token":
        raise HTTPException(status_code=401, detail="Token inválido")
 
    return payload
