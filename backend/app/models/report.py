from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    location_id: Mapped[str] = mapped_column(
        ForeignKey("locations.id"), nullable=False, index=True
    )
    share_token: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)

    # Report sections stored as Markdown/JSON text
    market_overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    neighbourhood_insights: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    demographics_section: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    investment_intelligence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comparable_properties: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Aggregated market metrics for dashboard cards
    median_price: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    price_appreciation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    rental_yield: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    days_on_market: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    roi_estimate: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped["User"] = relationship(back_populates="reports")
    location: Mapped["Location"] = relationship(back_populates="reports")
