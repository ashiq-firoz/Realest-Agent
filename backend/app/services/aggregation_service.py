"""
AggregationService — orchestrates parallel fetching from all external data sources.

Uses asyncio.gather with return_exceptions=True so that a single API failure
does not abort the pipeline. Failed sources are substituted with mock data,
and the affected data records are marked is_stale=True.

Real free sources: PropertyLens (comparable listings), ABS Census 2021 POA
(demographics + median rent), ABS RPPI (price appreciation), OpenStreetMap
Overpass (neighbourhood amenities). Price/yield/days-on-market are estimated.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aggregated_data import AggregatedMarketData
from app.schemas.location import LocationSummary
from app.schemas.report import (
    AggregatedDataBundle,
    AmenitiesSnapshot,
    MetricValue,
)
from app.services.abs_service import ABSService, MOCK_DEMOGRAPHICS
from app.services.amenities_service import AmenitiesService, _unavailable
from app.services.domain_service import PropertyLensService
from app.services.govdata_service import GovDataService, MOCK_MARKET_METRICS

logger = logging.getLogger(__name__)


class AggregationService:
    """
    Orchestrates data fetching from PropertyLens, ABS, GovData (RPPI) and OSM in
    parallel. Substitutes mock data for any source that fails and writes results
    to the aggregated_market_data table.
    """

    def __init__(self) -> None:
        self._domain = PropertyLensService()
        self._abs = ABSService()
        self._govdata = GovDataService()
        self._amenities = AmenitiesService()

    async def aggregate_for_location(
        self,
        location: LocationSummary,
        db: AsyncSession,
    ) -> AggregatedDataBundle:
        """Run all data sources in parallel, merge with fallbacks, persist, and return."""
        results = await asyncio.gather(
            self._domain.fetch_listings(location),
            self._abs.fetch_demographics(location),
            self._govdata.fetch_market_data(location),
            self._amenities.fetch_amenities(location),
            return_exceptions=True,
        )

        bundle = self._merge_with_fallbacks(results, location)

        # Persist results to DB
        await self._persist(location.id, results, db)

        return bundle

    def _merge_with_fallbacks(
        self,
        results: tuple[Any, Any, Any, Any],
        location: LocationSummary | None = None,
    ) -> AggregatedDataBundle:
        """Substitute mock data for any failed source and overlay real ABS rent."""
        domain_result, abs_result, govdata_result, amenities_result = results
        is_stale = False

        if isinstance(domain_result, Exception):
            logger.warning("PropertyLens failed; no comparable listings: %s", domain_result)
            listings = []
            is_stale = True
        else:
            listings = domain_result

        if isinstance(abs_result, Exception):
            logger.warning("ABS API failed, using mock demographics: %s", abs_result)
            demographics = MOCK_DEMOGRAPHICS
            is_stale = True
        else:
            demographics = abs_result

        if isinstance(govdata_result, Exception):
            logger.warning("GovData/RPPI failed, using mock market metrics: %s", govdata_result)
            market_metrics = MOCK_MARKET_METRICS
            is_stale = True
        else:
            market_metrics = govdata_result

        if isinstance(amenities_result, Exception):
            logger.warning("Overpass failed, using neutral amenities: %s", amenities_result)
            amenities: AmenitiesSnapshot = _unavailable(location)
            is_stale = True
        else:
            amenities = amenities_result

        # Overlay the REAL ABS Census median rent onto the (estimated) market metrics
        # and recompute rental yield against the estimated sale price. Use model_copy
        # so we never mutate a shared singleton (e.g. MOCK_MARKET_METRICS).
        real_rent = getattr(demographics, "median_rent_weekly", None)
        if real_rent:
            today = date.today().isoformat()
            updates: dict[str, Any] = {
                "median_rent_weekly": MetricValue(
                    value=int(real_rent), source="abs_census_2021", date=today
                )
            }
            price = getattr(market_metrics.median_sale_price, "value", None)
            if price:
                updates["rental_yield"] = MetricValue(
                    value=round(int(real_rent) * 52 / price * 100, 1),
                    source="estimate",
                    date=today,
                )
            market_metrics = market_metrics.model_copy(update=updates)

        return AggregatedDataBundle(
            listings=listings,
            demographics=demographics,
            market_metrics=market_metrics,
            amenities=amenities,
            is_stale=is_stale,
        )

    async def _persist(
        self,
        location_id: str,
        results: tuple[Any, Any, Any, Any],
        db: AsyncSession,
    ) -> None:
        """Persist each source's result to the aggregated_market_data table."""
        domain_result, abs_result, govdata_result, amenities_result = results

        # PropertyLens listings
        is_domain_stale = isinstance(domain_result, Exception)
        domain_data = (
            [] if is_domain_stale
            else [listing.model_dump() for listing in domain_result]
        )
        db.add(
            AggregatedMarketData(
                location_id=location_id,
                data_source="none" if is_domain_stale else "propertylens",
                data_type="listings",
                payload=json.dumps(domain_data),
                is_stale=is_domain_stale,
            )
        )

        # ABS demographics
        is_abs_stale = isinstance(abs_result, Exception)
        abs_data = MOCK_DEMOGRAPHICS.model_dump() if is_abs_stale else abs_result.model_dump()
        db.add(
            AggregatedMarketData(
                location_id=location_id,
                data_source="mock" if is_abs_stale else "abs",
                data_type="demographics",
                payload=json.dumps(abs_data),
                is_stale=is_abs_stale,
            )
        )

        # Market metrics (ABS RPPI + estimates)
        is_govdata_stale = isinstance(govdata_result, Exception)
        govdata_data = (
            MOCK_MARKET_METRICS.model_dump() if is_govdata_stale else govdata_result.model_dump()
        )
        db.add(
            AggregatedMarketData(
                location_id=location_id,
                data_source="mock" if is_govdata_stale else "govdata",
                data_type="market",
                payload=json.dumps(govdata_data),
                is_stale=is_govdata_stale,
            )
        )

        # OSM amenities
        is_amenities_stale = isinstance(amenities_result, Exception)
        amenities_data = (
            _unavailable().model_dump() if is_amenities_stale else amenities_result.model_dump()
        )
        db.add(
            AggregatedMarketData(
                location_id=location_id,
                data_source="osm" if not is_amenities_stale else "mock",
                data_type="amenities",
                payload=json.dumps(amenities_data),
                is_stale=is_amenities_stale,
            )
        )
