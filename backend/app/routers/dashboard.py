"""
Dashboard router — reports, saved locations, and investment analytics endpoints.
"""
# from __future__ import annotations

from fastapi import Response


import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, require_pro
from app.models.location import Location
from app.models.report import Report
from app.models.saved_location import SavedLocation
from app.models.user import User
from app.schemas.dashboard import (
    DashboardReport,
    InvestmentAnalyticsEntry,
    SavedLocationResponse,
)
from app.schemas.location import LocationSummary

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# GET /dashboard/reports
# ---------------------------------------------------------------------------

@router.get("/reports", response_model=List[DashboardReport])
async def get_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DashboardReport]:
    """
    Return the 20 most recent non-deleted reports for the current user,
    with associated location details.
    """
    result = await db.execute(
        select(Report)
        .where(
            Report.user_id == current_user.id,
            Report.is_deleted.is_(False),
        )
        .order_by(Report.created_at.desc())
        .limit(20)
    )
    reports = result.scalars().all()

    # Eagerly load associated locations
    location_ids = list({r.location_id for r in reports})
    locations: dict[str, Location] = {}
    if location_ids:
        loc_result = await db.execute(
            select(Location).where(Location.id.in_(location_ids))
        )
        locations = {loc.id: loc for loc in loc_result.scalars().all()}

    output: List[DashboardReport] = []
    for report in reports:
        loc = locations.get(report.location_id)
        if loc is None:
            continue
        output.append(
            DashboardReport(
                id=report.id,
                location=LocationSummary.model_validate(loc),
                created_at=report.created_at,
                median_price=report.median_price,
                share_token=report.share_token,
            )
        )
    return output


# ---------------------------------------------------------------------------
# POST /dashboard/saved-locations
# ---------------------------------------------------------------------------

from pydantic import BaseModel


class SavedLocationCreate(BaseModel):
    location_id: str


@router.post(
    "/saved-locations",
    response_model=SavedLocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_location(
    body: SavedLocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_pro),
) -> SavedLocationResponse:
    """
    Save a location for the current Pro user.
    If the location is already saved, return the existing record (upsert).
    """
    # Verify location exists
    loc_result = await db.execute(
        select(Location).where(Location.id == body.location_id)
    )
    location = loc_result.scalar_one_or_none()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {body.location_id} not found",
        )

    # Check if already saved (upsert behaviour)
    existing_result = await db.execute(
        select(SavedLocation).where(
            SavedLocation.user_id == current_user.id,
            SavedLocation.location_id == body.location_id,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        saved = existing
    else:
        saved = SavedLocation(
            user_id=current_user.id,
            location_id=body.location_id,
        )
        db.add(saved)
        await db.commit()
        await db.refresh(saved)

    return SavedLocationResponse(
        id=saved.id,
        location=LocationSummary.model_validate(location),
        created_at=saved.created_at,
    )


# ---------------------------------------------------------------------------
# GET /dashboard/saved-locations
# ---------------------------------------------------------------------------

@router.get("/saved-locations", response_model=List[SavedLocationResponse])
async def get_saved_locations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_pro),
) -> List[SavedLocationResponse]:
    """
    Return all saved locations for the current Pro user with location details.
    """
    result = await db.execute(
        select(SavedLocation).where(SavedLocation.user_id == current_user.id)
    )
    saved_locations = result.scalars().all()

    location_ids = [sl.location_id for sl in saved_locations]
    locations: dict[str, Location] = {}
    if location_ids:
        loc_result = await db.execute(
            select(Location).where(Location.id.in_(location_ids))
        )
        locations = {loc.id: loc for loc in loc_result.scalars().all()}

    output: List[SavedLocationResponse] = []
    for sl in saved_locations:
        loc = locations.get(sl.location_id)
        if loc is None:
            continue
        output.append(
            SavedLocationResponse(
                id=sl.id,
                location=LocationSummary.model_validate(loc),
                created_at=sl.created_at,
            )
        )
    return output


# ---------------------------------------------------------------------------
# DELETE /dashboard/saved-locations/{id}
# ---------------------------------------------------------------------------

@router.delete("/saved-locations/{saved_location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_location(
    saved_location_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_pro),
):
    """
    Delete a saved location. Returns 404 if it doesn't exist or isn't owned by the current user.
    """
    result = await db.execute(
        select(SavedLocation).where(
            SavedLocation.id == saved_location_id,
            SavedLocation.user_id == current_user.id,
        )
    )
    saved = result.scalar_one_or_none()
    if not saved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved location not found",
        )
    await db.delete(saved)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# GET /dashboard/analytics
# ---------------------------------------------------------------------------

async def _get_analytics_entries(db: AsyncSession, current_user: User) -> List[InvestmentAnalyticsEntry]:
    # Fetch saved locations for this user
    sl_result = await db.execute(
        select(SavedLocation).where(SavedLocation.user_id == current_user.id)
    )
    saved_locations = sl_result.scalars().all()

    if not saved_locations:
        return []

    location_ids = [sl.location_id for sl in saved_locations]

    # Fetch all locations
    loc_result = await db.execute(
        select(Location).where(Location.id.in_(location_ids))
    )
    locations: dict[str, Location] = {loc.id: loc for loc in loc_result.scalars().all()}

    # For each location, get the latest non-deleted report
    reports_result = await db.execute(
        select(Report)
        .where(
            Report.location_id.in_(location_ids),
            Report.is_deleted.is_(False),
        )
        .order_by(Report.location_id, Report.created_at.desc())
    )
    all_reports = reports_result.scalars().all()

    # Keep only the latest report per location_id
    latest_report_per_location: dict[str, Report] = {}
    for report in all_reports:
        if report.location_id not in latest_report_per_location:
            latest_report_per_location[report.location_id] = report

    # Build analytics entries
    entries: List[InvestmentAnalyticsEntry] = []
    for location_id in location_ids:
        loc = locations.get(location_id)
        if loc is None:
            continue
        report = latest_report_per_location.get(location_id)
        entries.append(
            InvestmentAnalyticsEntry(
                location=LocationSummary.model_validate(loc),
                roi_estimate=report.roi_estimate if report else None,
                rental_yield=report.rental_yield if report else None,
                median_price=report.median_price if report else None,
            )
        )

    # Sort by roi_estimate descending (treat None as lowest)
    def _roi_sort_key(entry: InvestmentAnalyticsEntry):
        val = entry.roi_estimate
        if val is None:
            return float("-inf")
        # Strip common suffixes like "%" and try to parse as float
        try:
            return float(val.strip().rstrip("%").replace(",", ""))
        except (ValueError, AttributeError):
            return float("-inf")

    entries.sort(key=_roi_sort_key, reverse=True)
    return entries


@router.get("/analytics", response_model=List[InvestmentAnalyticsEntry])
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_pro),
) -> List[InvestmentAnalyticsEntry]:
    """
    Return investment analytics for each saved location.
    """
    return await _get_analytics_entries(db, current_user)


from app.models.insight import StoredInsight

@router.get("/analytics/insights")
async def get_analytics_insights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_pro),
):
    """
    Return the cached AI-generated text insight comparing the user's saved locations.
    """
    result = await db.execute(
        select(StoredInsight)
        .where(
            StoredInsight.insight_type == "dashboard_analytics",
            StoredInsight.reference_id == current_user.id
        )
    )
    insight = result.scalar_one_or_none()
    
    if insight:
        return {"insight": insight.content, "updated_at": insight.updated_at}
    else:
        return {"insight": None, "updated_at": None}

@router.post("/analytics/insights/reanalyze")
async def reanalyze_analytics_insights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_pro),
):
    """
    Generate a fresh AI insight and store it in the database.
    """
    entries = await _get_analytics_entries(db, current_user)
    
    from app.services.gemini_service import GeminiService
    gemini_service = GeminiService()
    
    data_dicts = [e.model_dump() for e in entries]
    new_insight_text = await gemini_service.generate_investment_insights(data_dicts)
    
    result = await db.execute(
        select(StoredInsight)
        .where(
            StoredInsight.insight_type == "dashboard_analytics",
            StoredInsight.reference_id == current_user.id
        )
    )
    insight = result.scalar_one_or_none()
    
    if insight:
        insight.content = new_insight_text
    else:
        insight = StoredInsight(
            insight_type="dashboard_analytics",
            reference_id=current_user.id,
            content=new_insight_text
        )
        db.add(insight)
        
    await db.commit()
    await db.refresh(insight)
    
    return {"insight": insight.content, "updated_at": insight.updated_at}
