from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AgentChat(Base):
    __tablename__ = "agent_chats"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="agent_chats")
    messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    chat_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_chats.id"), index=True)
    role: Mapped[str] = mapped_column(String(50))  # 'user', 'model', 'system', 'tool'
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_calls: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # store tool calls or tool results if needed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    chat: Mapped["AgentChat"] = relationship(back_populates="messages")
