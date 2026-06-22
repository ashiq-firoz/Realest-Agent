from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class GeographicIdentity(BaseModel):
    """Canonical geographic identity object to ensure geographic integrity."""
    country: str
    state: str
    city: str
    suburb: Optional[str] = None
    postcode: Optional[str] = None
    latitude: float
    longitude: float


class GeographyMetadata(BaseModel):
    """Metadata for datasets to track geographic source."""
    geography_type: str  # e.g., "postcode", "suburb", "city", "lga", "state"
    geography_id: str    # e.g., "2000", "Sydney", "NSW"
    source: str          # e.g., "CoreLogic", "ABS", "Domain"
    as_of_date: str      # e.g., "2026-06", "2026-06-17"
