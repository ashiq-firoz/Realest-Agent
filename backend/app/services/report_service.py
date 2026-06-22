"""
ReportService — orchestrates report generation end-to-end.

Steps:
1. Load Location by location_id; raise LocationNotFoundError if absent.
2. Get aggregated data from cache; on miss, call AggregationService and cache result.
3. Call GeminiService.generate_report with a 30-second timeout.
4. Persist Report row with all 6 sections + extracted metrics; return ReportResponse.
"""
from __future__ import annotations

import asyncio
import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.models.report import Report
from app.schemas.location import LocationSummary
from app.schemas.report import AggregatedDataBundle, ReportResponse
from app.services.aggregation_service import AggregationService
from app.services.cache_service import get_cache_service
from app.services.gemini_service import GeminiService
from app.services.geo_service import GeoService
from app.utils.token import generate_share_token

logger = logging.getLogger(__name__)


class LocationNotFoundError(Exception):
    """Raised when the requested location_id does not exist in the database."""


class ReportGenerationError(Exception):
    """Raised when report generation fails (e.g., timeout)."""


def _location_to_summary(location: Location) -> LocationSummary:
    """Convert ORM Location to LocationSummary Pydantic model."""
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


class ReportService:
    def __init__(self) -> None:
        self._cache = get_cache_service()
        self._aggregation = AggregationService()
        self._gemini = GeminiService()
        self._geo = GeoService()

    async def create_report(
        self,
        user_id: str,
        location_id: str,
        db: AsyncSession,
    ) -> ReportResponse:
        """
        Generate and persist a new intelligence report for the given location.

        Raises:
            LocationNotFoundError: if location_id does not exist.
            ReportGenerationError: if Gemini times out (> 30 s).
        """
        # ── Step 1: Load Location ─────────────────────────────────────────
        result = await db.execute(
            select(Location).where(Location.id == location_id)
        )
        location_orm = result.scalar_one_or_none()
        
        # If not in DB, it might be dynamically generated from GeoService.
        if location_orm is None:
            mem_loc = await self._geo.get_location_by_id(location_id)
            if not mem_loc:
                raise LocationNotFoundError(f"Location '{location_id}' not found.")
            
            # Save it to DB
            location_orm = Location(
                id=mem_loc.id,
                display_name=mem_loc.display_name,
                suburb=mem_loc.suburb,
                city=mem_loc.city,
                state=mem_loc.state,
                postcode=mem_loc.postcode,
                country_code=mem_loc.country_code,
                latitude=mem_loc.latitude,
                longitude=mem_loc.longitude,
            )
            db.add(location_orm)
            await db.commit()
            await db.refresh(location_orm)

        location = _location_to_summary(location_orm)

        # ── Step 1.5: Check for existing report for this location ─────────
        existing_report_result = await db.execute(
            select(Report).where(Report.location_id == location_id).order_by(Report.created_at.desc()).limit(1)
        )
        existing_report = existing_report_result.scalar_one_or_none()

        if existing_report:
            logger.info("Found existing report for location %s. Reusing it.", location_id)
            share_token = generate_share_token()
            report = Report(
                user_id=user_id,
                location_id=location_id,
                share_token=share_token,
                market_overview=existing_report.market_overview,
                neighbourhood_insights=existing_report.neighbourhood_insights,
                demographics_section=existing_report.demographics_section,
                investment_intelligence=existing_report.investment_intelligence,
                comparable_properties=existing_report.comparable_properties,
                ai_summary=existing_report.ai_summary,
                median_price=existing_report.median_price,
                price_appreciation=existing_report.price_appreciation,
                rental_yield=existing_report.rental_yield,
                days_on_market=existing_report.days_on_market,
                roi_estimate=existing_report.roi_estimate,
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)

            comparable_properties = []
            if existing_report.comparable_properties:
                try:
                    from app.schemas.report import PropertyListing
                    comparable_properties = [
                        PropertyListing(**p) for p in json.loads(existing_report.comparable_properties)
                    ]
                except Exception as e:
                    logger.error("Failed to parse comparable properties: %s", e)

            return ReportResponse(
                id=report.id,
                share_token=report.share_token,
                location=location,
                market_overview=report.market_overview or "",
                neighbourhood_insights=report.neighbourhood_insights or "",
                demographics_section=report.demographics_section or "",
                investment_intelligence=report.investment_intelligence or "",
                comparable_properties=comparable_properties,
                ai_summary=report.ai_summary or "",
                median_price=report.median_price,
                price_appreciation=report.price_appreciation,
                rental_yield=report.rental_yield,
                days_on_market=report.days_on_market,
                roi_estimate=report.roi_estimate,
                created_at=report.created_at,
            )

        # ── Step 2: Aggregated data — cache-first ─────────────────────────
        aggregated: AggregatedDataBundle | None = await self._cache.get_aggregated(location_id)
        if aggregated is None:
            logger.info("Cache miss for location %s — aggregating data.", location_id)
            aggregated = await self._aggregation.aggregate_for_location(location, db)
            await self._cache.set_aggregated(location_id, aggregated)


        # ── Step 3: Gemini report generation (30 s timeout) ───────────────
        try:
            sections: dict[str, str] = await asyncio.wait_for(
                self._gemini.generate_report(location, aggregated),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            raise ReportGenerationError("Report generation timed out")

        def metric_value(metric):
            if metric is None:
                return None

            if hasattr(metric, "value"):
                return metric.value

            return metric

        # ── Step 4: Extract metrics, persist Report row, return response ──
       
        data = aggregated
        logger.info(
        "median_sale_price=%s type=%s",
        data.market_metrics.median_sale_price,
        type(data.market_metrics.median_sale_price),
        )
        # median_price = f"${data.market_metrics.median_sale_price:,}"
        # price_appreciation = f"{data.market_metrics.price_appreciation_yoy:.1f}%"
        # rental_yield = f"{data.market_metrics.rental_yield:.1f}%"
        # days_on_market = data.market_metrics.days_on_market
        # roi_estimate = f"{data.market_metrics.rental_yield:.1f}%"
        
        median_sale_price = metric_value(data.market_metrics.median_sale_price)
        price_appreciation_yoy = metric_value(data.market_metrics.price_appreciation_yoy)
        rental_yield_val = metric_value(data.market_metrics.rental_yield)
        days_on_market_val = metric_value(data.market_metrics.days_on_market)

        median_price = (
            f"${median_sale_price:,}"
            if median_sale_price is not None
            else "N/A"
        )

        price_appreciation = (
            f"{price_appreciation_yoy:.1f}%"
            if price_appreciation_yoy is not None
            else "N/A"
        )

        rental_yield = (
            f"{rental_yield_val:.1f}%"
            if rental_yield_val is not None
            else "N/A"
        )

        days_on_market = days_on_market_val
        roi_estimate = rental_yield
                

        share_token = generate_share_token()

        report = Report(
            user_id=user_id,
            location_id=location_id,
            share_token=share_token,
            market_overview=sections.get("Market Overview", ""),
            neighbourhood_insights=sections.get("Neighbourhood Insights", ""),
            demographics_section=sections.get("Demographics", ""),
            investment_intelligence=sections.get("Investment Intelligence", ""),
            comparable_properties=json.dumps(
                [p.model_dump() for p in aggregated.listings]
            ),
            ai_summary=sections.get("AI Summary", ""),
            median_price=median_price,
            price_appreciation=price_appreciation,
            rental_yield=rental_yield,
            days_on_market=days_on_market,
            roi_estimate=roi_estimate,
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        return ReportResponse(
            id=report.id,
            share_token=report.share_token,
            location=location,
            market_overview=report.market_overview or "",
            neighbourhood_insights=report.neighbourhood_insights or "",
            demographics_section=report.demographics_section or "",
            investment_intelligence=report.investment_intelligence or "",
            comparable_properties=aggregated.listings,
            ai_summary=report.ai_summary or "",
            median_price=report.median_price,
            price_appreciation=report.price_appreciation,
            rental_yield=report.rental_yield,
            days_on_market=report.days_on_market,
            roi_estimate=report.roi_estimate,
            created_at=report.created_at,
        )
