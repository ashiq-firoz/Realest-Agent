"""
Locations router — autocomplete and location detail endpoints.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.location import Location
from app.models.user import User
from app.schemas.location import AutocompleteResponse, LocationSummary
from app.services.geo_service import GeoService, GeocodeError

logger = logging.getLogger(__name__)
router = APIRouter()
geo_service = GeoService()


@router.get("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(
    q: str = Query(..., min_length=1, description="Search query"),
) -> AutocompleteResponse:
    """
    Autocomplete location search using Nominatim.
    No authentication required. Returns ≤ 8 Australian locations.
    """
    try:
        results = await geo_service.autocomplete(q)
    except GeocodeError as exc:
        logger.warning("Geocode error for query %r: %s", q, exc)
        # Return empty results on geocode failure (don't 503 the client)
        results = []
    return AutocompleteResponse(results=results)


@router.get("/{location_id}", response_model=LocationSummary)
async def get_location(
    location_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LocationSummary:
    """
    Get location details by ID. Requires JWT authentication.
    """
    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found",
        )
    return LocationSummary.model_validate(location)
