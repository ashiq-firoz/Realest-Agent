from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import BigInteger, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    display_name: Mapped[str] = mapped_column(String(512), nullable=False)
    suburb: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postcode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="Australia")
    country_code: Mapped[str] = mapped_column(String(3), default="AU")
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    nominatim_place_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    reports: Mapped[List["Report"]] = relationship(back_populates="location")
    aggregated_data: Mapped[List["AggregatedMarketData"]] = relationship(
        back_populates="location"
    )
