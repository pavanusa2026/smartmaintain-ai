from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

security = HTTPBearer(auto_error=False)

ROLES = {
    "admin": ["admin", "supervisor", "technician", "operator", "inspector", "manager", "engineer"],
    "supervisor": ["supervisor", "technician", "operator", "inspector"],
    "technician": ["technician"],
    "operator": ["operator"],
    "inspector": ["inspector"],
    "manager": ["manager", "supervisor"],
    "engineer": ["engineer", "technician"],
}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict[str, Any]) -> str:
    settings = get_settings()
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials)
        return {
            "userId": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "operator"),
            "name": payload.get("name", "User"),
        }
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def require_roles(*allowed: str):
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        role = user.get("role", "")
        if role == "admin" or role in allowed:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    return checker
