from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    image: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), default="credentials")
    tier: Mapped[str] = mapped_column(String(20), default="regular")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    reports: Mapped[List["Report"]] = relationship(back_populates="user")
    saved_locations: Mapped[List["SavedLocation"]] = relationship(back_populates="user")
    watchlist_entries: Mapped[List["WatchlistEntry"]] = relationship(back_populates="user")
    agent_chats: Mapped[List["AgentChat"]] = relationship(back_populates="user", cascade="all, delete-orphan")
