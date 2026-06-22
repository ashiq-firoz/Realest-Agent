from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    # User chooses their mode at signup; no payment required. Defaults to regular.
    tier: Literal["regular", "pro"] = "regular"

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tier: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    image: Optional[str]
    provider: str
    tier: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
