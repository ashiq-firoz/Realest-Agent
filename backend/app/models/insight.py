from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StoredInsight(Base):
    __tablename__ = "stored_insights"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    insight_type: Mapped[str] = mapped_column(String(50), index=True) # e.g. 'suburb_analysis', 'property_insight'
    reference_id: Mapped[str] = mapped_column(String(255), index=True) # e.g. suburb slug or property id
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
