"""
Reports router — create, retrieve, share, delete, and export reports.

Endpoints:
    POST   /reports                   — create a new report (JWT)
    GET    /reports/share/{token}     — public share link (no auth)
    GET    /reports/{id}              — get report by ID (JWT, owner check)
    DELETE /reports/{id}              — soft-delete report (JWT, owner check)
    GET    /reports/{id}/export/pdf   — stream PDF export (JWT)

NOTE: The share/{token} route is declared BEFORE the {id} route to prevent
FastAPI from matching the literal string "share" as a report ID.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.location import Location
from app.models.report import Report
from app.models.user import User
from app.schemas.location import LocationSummary
from app.schemas.report import ReportGenerationRequest, ReportResponse
from app.services.cache_service import get_cache_service
from app.services.pdf_service import PDFService
from app.services.report_service import LocationNotFoundError, ReportService

logger = logging.getLogger(__name__)

router = APIRouter()

_report_service = ReportService()
_pdf_service = PDFService()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _location_to_summary(location: Location) -> LocationSummary:
    """Convert a Location ORM instance to a LocationSummary schema."""
    return LocationSummary(
        id=location.id,
        display_name=location.display_name,
        suburb=location.suburb,
        city=location.city,
        state=location.state,
        postcode=location.postcode,
        country_code=location.country_code,
        latitude=location.latitude,
        longitude=location.longitude,
    )


async def _build_report_response(report: Report, db: AsyncSession) -> ReportResponse:
    """
    Build a ReportResponse from a Report ORM object, loading the related
    Location and deserialising comparable_properties from JSON.
    """
    import json

    location_orm = await db.get(Location, report.location_id)
    if location_orm is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Report location could not be found.",
        )

    location_summary = _location_to_summary(location_orm)

    from app.schemas.report import PropertyListing

    raw_listings = json.loads(report.comparable_properties or "[]")
    listings = [PropertyListing.model_validate(p) for p in raw_listings]

    return ReportResponse(
        id=report.id,
        share_token=report.share_token,
        location=location_summary,
        market_overview=report.market_overview or "",
        neighbourhood_insights=report.neighbourhood_insights or "",
        demographics_section=report.demographics_section or "",
        investment_intelligence=report.investment_intelligence or "",
        comparable_properties=listings,
        ai_summary=report.ai_summary or "",
        median_price=report.median_price,
        price_appreciation=report.price_appreciation,
        rental_yield=report.rental_yield,
        days_on_market=report.days_on_market,
        roi_estimate=report.roi_estimate,
        created_at=report.created_at,
    )


# ---------------------------------------------------------------------------
# POST /reports — create a new report
# ---------------------------------------------------------------------------

@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    body: ReportGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportResponse:
    """
    Generate and persist a new intelligence report for the given location.

    Requirements: 3.4, 4.1
    """
    try:
        report_response = await _report_service.create_report(
            user_id=current_user.id,
            location_id=body.location_id,
            db=db,
        )
    except LocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return report_response


# ---------------------------------------------------------------------------
# GET /reports/share/{token} — public share endpoint (NO auth)
# NOTE: Must be declared before GET /reports/{id} to avoid path conflicts.
# ---------------------------------------------------------------------------

@router.get("/share/{token}", response_model=ReportResponse)
async def get_shared_report(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """
    Retrieve a report by its public share token.
    No authentication required.
    Returns 404 if the token is invalid or the report is soft-deleted.

    Requirements: 4.6, 5.1
    """
    result = await db.execute(
        select(Report).where(Report.share_token == token)
    )
    report = result.scalar_one_or_none()

    if report is None or report.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    return await _build_report_response(report, db)


# ---------------------------------------------------------------------------
# GET /reports/{id} — get report by ID (JWT, owner check, cached)
# ---------------------------------------------------------------------------

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportResponse:
    """
    Retrieve a report by its ID.
    - Returns 404 if the report does not exist or is soft-deleted.
    - Returns 403 if the current user is not the report owner.
    - Result is cached for 24 hours.

    Requirements: 4.5, 5.3
    """
    cache = get_cache_service()

    # ── Cache-first lookup ────────────────────────────────────────────────
    cached = await cache.get_report(report_id)
    if cached is not None:
        # Still enforce ownership even on cache hit
        if cached.id != report_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
        # We need the actual report owner_id to check ownership; query DB for ownership check
        result = await db.execute(select(Report).where(Report.id == report_id))
        report_orm = result.scalar_one_or_none()
        if report_orm is None or report_orm.is_deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
        if report_orm.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        return cached

    # ── DB lookup ─────────────────────────────────────────────────────────
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()

    if report is None or report.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    report_response = await _build_report_response(report, db)

    # ── Cache for 24 h ────────────────────────────────────────────────────
    await cache.set_report(report_id, report_response)

    return report_response


# ---------------------------------------------------------------------------
# DELETE /reports/{id} — soft-delete (JWT, owner check)
# ---------------------------------------------------------------------------

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft-delete a report by setting is_deleted=True.
    - Returns 404 if not found or already deleted.
    - Returns 403 if the current user is not the report owner.
    - Invalidates the report cache entry.

    Requirements: 4.5, 6.4
    """
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()

    if report is None or report.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    report.is_deleted = True
    await db.commit()

    # Invalidate report cache
    cache = get_cache_service()
    # CacheService uses "report:{id}" key pattern — delete via internal Redis key
    try:
        await cache._redis.delete(f"report:{report_id}")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to invalidate cache for report %s: %s", report_id, exc)


# ---------------------------------------------------------------------------
# GET /reports/{id}/export/pdf — stream PDF export (JWT)
# ---------------------------------------------------------------------------

@router.get("/{report_id}/export/pdf")
async def export_report_pdf(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Generate and stream a PDF export of the report.
    - Returns 404 if not found or soft-deleted.
    - Returns 403 if the current user is not the report owner.
    - Streams the PDF as application/pdf with a Content-Disposition attachment header.

    Requirements: 5.1, 5.3
    """
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()

    if report is None or report.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    report_response = await _build_report_response(report, db)

    pdf_bytes = _pdf_service.generate(report_response)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="report-{report_id}.pdf"',
        },
    )
