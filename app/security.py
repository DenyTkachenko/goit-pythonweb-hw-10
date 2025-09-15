from datetime import datetime, timedelta
from typing import Any, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def _create_token(subject: str | int, token_type: str, minutes: int) -> str:
    exp = datetime.utcnow() + timedelta(minutes=minutes)
    payload = {"sub": str(subject), "type": token_type, "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def create_access_token(user_id: int) -> str:
    return _create_token(user_id, "access", settings.ACCESS_TOKEN_EXPIRE_MINUTES)

def create_verify_token(user_id: int) -> str:
    return _create_token(user_id, "verify", settings.VERIFY_TOKEN_EXPIRE_MINUTES)

def decode_token(token: str) -> Optional[dict[str, Any]]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except JWTError:
        return None
