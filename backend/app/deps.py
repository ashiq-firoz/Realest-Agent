"""
FastAPI dependency injection — DB session, current user, Pro gate.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.token import decode_jwt

# auto_error=False so a MISSING Authorization header yields 401 (handled below),
# not the default 403 — the frontend treats 401 as "redirect to login".
security = HTTPBearer(auto_error=False)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate the Bearer JWT (issued by the backend, signed with NEXTAUTH_SECRET),
    resolve the user by its `sub` claim, and attach it to the request.

    Raises 401 if the token is missing, invalid, expired, or the user is unknown.
    """
    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    try:
        payload = decode_jwt(token)
    except JWTError:
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception

    return user


async def require_pro(user: User = Depends(get_current_user)) -> User:
    """
    Pro gate. Intentionally permissive for now: both Regular and Pro users may
    access every feature (the platform exposes all features to all tiers). It is
    still backed by real per-user authentication via get_current_user, so it can
    be tightened later by checking `user.tier == "pro"`.
    """
    return user
