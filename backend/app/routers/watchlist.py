"""
Watchlist router — manage pro-user watchlist entries with price sparkline data.
"""
# from __future__ import annotations
from fastapi import Response

import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_pro
from app.models.aggregated_data import AggregatedMarketData
from app.models.location import Location
from app.models.user import User
from app.models.watchlist import WatchlistEntry
from app.schemas.dashboard import WatchlistEntryResponse
from app.schemas.location import LocationSummary

logger = logging.getLogger(__name__)
router = APIRouter()


class WatchlistCreateRequest(BaseModel):
    location_id: str


@router.post("", response_model=WatchlistEntryResponse, status_code=status.HTTP_201_CREATED)
async def add_watchlist_entry(
    body: WatchlistCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_pro),
) -> WatchlistEntryResponse:
    """
    Add a location to the current user's watchlist.
    Requires JWT authentication and Pro tier.
    Returns the created WatchlistEntryResponse.
    """
    # Verify the location exists
    location_result = await db.execute(
        select(Location).where(Location.id == body.location_id)
    )
    location = location_result.scalar_one_or_none()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {body.location_id} not found",
        )

    # Create the watchlist entry
    entry = WatchlistEntry(
        user_id=current_user.id,
        location_id=body.location_id,
    )
    db.add(entry)
    try:
        await db.commit()
        await db.refresh(entry)
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Location already in watchlist",
        )

    return WatchlistEntryResponse(
        id=entry.id,
        location=LocationSummary.model_validate(location),
        price_history=[],
        created_at=entry.created_at,
    )


@router.get("", response_model=List[WatchlistEntryResponse])
async def get_watchlist(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_pro),
) -> List[WatchlistEntryResponse]:
    """
    Get the current user's watchlist with sparkline price history.
    Requires JWT authentication and Pro tier.
    Returns list of WatchlistEntryResponse with last 12 median_sale_price data points.
    """
    # Fetch all watchlist entries for current user, joining location
    entries_result = await db.execute(
        select(WatchlistEntry, Location)
        .join(Location, WatchlistEntry.location_id == Location.id)
        .where(WatchlistEntry.user_id == current_user.id)
        .order_by(desc(WatchlistEntry.created_at))
    )
    rows = entries_result.all()

    responses: List[WatchlistEntryResponse] = []
    for entry, location in rows:
        # Fetch last 12 aggregated_market_data records for this location where data_type="market"
        market_data_result = await db.execute(
            select(AggregatedMarketData)
            .where(
                AggregatedMarketData.location_id == location.id,
                AggregatedMarketData.data_type == "market",
            )
            .order_by(desc(AggregatedMarketData.fetched_at))
            .limit(12)
        )
        market_records = market_data_result.scalars().all()

        # Extract median_sale_price from each JSON payload (oldest first for sparkline)
        price_history: List[float] = []
        for record in reversed(market_records):
            try:
                payload = json.loads(record.payload)
                price = payload.get("median_sale_price")
                if price is not None:
                    price_history.append(float(price))
            except (json.JSONDecodeError, ValueError, TypeError):
                logger.warning(
                    "Failed to parse median_sale_price from record %s", record.id
                )

        responses.append(
            WatchlistEntryResponse(
                id=entry.id,
                location=LocationSummary.model_validate(location),
                price_history=price_history,
                created_at=entry.created_at,
            )
        )

    return responses


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_pro),
):
    """
    Delete a watchlist entry owned by the current user.
    Requires JWT authentication and Pro tier.
    Returns 404 if entry not found or not owned by current user.
    """
    result = await db.execute(
        select(WatchlistEntry).where(
            WatchlistEntry.id == entry_id,
            WatchlistEntry.user_id == current_user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist entry not found",
        )

    await db.delete(entry)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)