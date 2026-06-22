"""
Token utilities for JWT generation and short share token generation.
"""
import secrets
import time
from typing import Any

from jose import jwt

from app.config import settings


def generate_share_token() -> str:
    """
    Generate a unique 8-character URL-safe token for report sharing.
    Characters: alphanumeric + '-' and '_' (URL-safe base64).
    Uses secrets.token_urlsafe which returns URL-safe base64 characters.
    Slices to exactly 8 characters.
    """
    # token_urlsafe(6) gives ~8 base64 chars; take first 8 to be safe
    while True:
        token = secrets.token_urlsafe(8)[:8]
        # Ensure all chars are URL-safe (token_urlsafe guarantees this)
        if len(token) == 8:
            return token


def create_jwt(user_id: str, tier: str) -> str:
    """
    Create a HS256 JWT signed with NEXTAUTH_SECRET.

    Claims:
        sub: user_id
        tier: user tier ("regular" | "pro")
        iat: issued at (Unix timestamp)
        exp: expires at (iat + 86400 seconds = 24 hours)

    Returns the encoded JWT string.
    """
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tier": tier,
        "iat": now,
        "exp": now + 86400,  # 24 hours
    }
    return jwt.encode(payload, settings.NEXTAUTH_SECRET, algorithm="HS256")


def decode_jwt(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT signed with NEXTAUTH_SECRET.
    Raises jose.JWTError on invalid/expired tokens.
    """
    return jwt.decode(token, settings.NEXTAUTH_SECRET, algorithms=["HS256"])
