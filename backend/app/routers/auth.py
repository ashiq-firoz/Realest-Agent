"""
Auth router — register, login, Google OAuth, and profile endpoints.
"""
from __future__ import annotations

import logging

import bcrypt
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.utils.token import create_jwt

logger = logging.getLogger(__name__)

router = APIRouter()

BCRYPT_ROUNDS = 12
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def hash_password(password: str) -> str:
    # Use the bcrypt library directly: passlib's bcrypt backend is broken with
    # bcrypt >= 4.1 (its wrap-bug self-test passes a >72-byte secret which bcrypt
    # now rejects). bcrypt only uses the first 72 bytes, so we truncate explicitly.
    pwd = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd, bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


class GoogleTokenRequest(BaseModel):
    # The Google OAuth access token (used as a Bearer token against userinfo).
    access_token: str
    # Mode chosen at signup; applied only when creating a brand-new user.
    tier: str = "regular"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Register a new user with email and password."""
    # Check for existing user
    result = await db.execute(select(User).where(User.email == body.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        name=body.name,
        provider="credentials",
        tier=body.tier,
    )
    db.add(user)
    await db.flush()  # get the generated id
    await db.refresh(user)

    token = create_jwt(user.id, user.tier)
    return TokenResponse(access_token=token, tier=user.tier)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Login with email and password."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_jwt(user.id, user.tier)
    return TokenResponse(access_token=token, tier=user.tier)


@router.post("/google", response_model=TokenResponse)
async def google_auth(
    body: GoogleTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange a Google OAuth access token for an app JWT. Upserts the user record."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {body.access_token}"},
            )
            resp.raise_for_status()
            google_user = resp.json()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to verify Google token: {exc}",
            ) from exc

    email = google_user.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account has no email",
        )

    # Upsert user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        chosen_tier = body.tier if body.tier in ("regular", "pro") else "regular"
        user = User(
            email=email,
            name=google_user.get("name"),
            image=google_user.get("picture"),
            provider="google",
            tier=chosen_tier,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
    else:
        # Update profile info on subsequent logins
        user.name = user.name or google_user.get("name")
        user.image = user.image or google_user.get("picture")
        if user.provider != "google":
            user.provider = "google"

    token = create_jwt(user.id, user.tier)
    return TokenResponse(access_token=token, tier=user.tier)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Get the current authenticated user's profile."""
    return current_user
