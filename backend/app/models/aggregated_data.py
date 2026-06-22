from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AggregatedMarketData(Base):
    __tablename__ = "aggregated_market_data"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    location_id: Mapped[str] = mapped_column(
        ForeignKey("locations.id"), nullable=False, index=True
    )
    data_source: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "domain" | "abs" | "govdata" | "mock"
    data_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "listings" | "demographics" | "market"
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON blob
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    location: Mapped["Location"] = relationship(back_populates="aggregated_data")
