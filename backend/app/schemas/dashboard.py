from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.location import LocationSummary


class DashboardReport(BaseModel):
    id: str
    location: LocationSummary
    created_at: datetime
    median_price: Optional[str] = None
    share_token: str

    model_config = ConfigDict(from_attributes=True)


class SavedLocationResponse(BaseModel):
    id: str
    location: LocationSummary
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistEntryResponse(BaseModel):
    id: str
    location: LocationSummary
    price_history: list[float] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestmentAnalyticsEntry(BaseModel):
    location: LocationSummary
    roi_estimate: Optional[str] = None
    rental_yield: Optional[str] = None
    median_price: Optional[str] = None
