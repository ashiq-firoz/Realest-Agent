from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class LocationSummary(BaseModel):
    id: str
    display_name: str
    suburb: Optional[str] = None
    city: str
    state: str
    postcode: Optional[str] = None
    country_code: str
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)


class AutocompleteResponse(BaseModel):
    results: list[LocationSummary]
