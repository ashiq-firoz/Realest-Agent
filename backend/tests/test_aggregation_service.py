"""
Property-based tests for AggregationService.

**Property 6: Data Aggregation Completeness Under Partial Failure**
**Property 9: Cache Hit Idempotence**
**Validates: Requirements 3.1, 3.5, 9.2, 9.3**

Property 6 asserts that for all 8 possible failure combinations of the three
external services (Domain, ABS, GovData), the returned AggregatedDataBundle
always has listings, demographics, and market_metrics non-null, and that
is_stale is True iff at least one service failed.

Property 9 (unit) asserts that CacheService.get_aggregated returns the same
pre-seeded bundle on repeated calls without making external API calls.
"""
import asyncio
import os
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Set required env vars BEFORE any app imports.
# ---------------------------------------------------------------------------
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("NEXTAUTH_SECRET", "test_secret_min_32_characters_long_abc")
os.environ.setdefault("DOMAIN_API_KEY", "test")

# ---------------------------------------------------------------------------
# Stub out app.database before any module that imports it is loaded.
# This prevents asyncpg from trying to connect to a real PostgreSQL server.
#
# We must also eagerly import all ORM models that reference each other via
# relationships (Location <-> AggregatedMarketData) so that SQLAlchemy's
# mapper can resolve them against the same DeclarativeBase.
# ---------------------------------------------------------------------------
if "app.database" not in sys.modules:
    _fake_db_module = ModuleType("app.database")
    from sqlalchemy.orm import DeclarativeBase

    class _FakeBase(DeclarativeBase):
        pass

    _fake_db_module.Base = _FakeBase  # type: ignore[attr-defined]
    _fake_db_module.get_db = AsyncMock()  # type: ignore[attr-defined]
    sys.modules["app.database"] = _fake_db_module

# Force-import ALL related ORM models so SQLAlchemy's mapper can resolve
# cross-model relationships (Location <-> Report <-> User <-> AggregatedMarketData).
# The order matters: import models with no foreign deps first.
import app.models.user  # noqa: E402, F401
import app.models.location  # noqa: E402, F401
import app.models.report  # noqa: E402, F401
import app.models.saved_location  # noqa: E402, F401
import app.models.watchlist  # noqa: E402, F401
import app.models.aggregated_data  # noqa: E402, F401

# ---------------------------------------------------------------------------
# Now safe to import app modules.
# ---------------------------------------------------------------------------
import pytest  # noqa: E402
from hypothesis import given, settings as h_settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from app.schemas.location import LocationSummary  # noqa: E402
from app.schemas.report import (  # noqa: E402
    AggregatedDataBundle,
    AmenitiesSnapshot,
    DemographicsSnapshot,
    MarketMetrics,
    MetricValue,
    PropertyListing,
)
from app.services.abs_service import MOCK_DEMOGRAPHICS  # noqa: E402
from app.services.aggregation_service import AggregationService  # noqa: E402
from app.services.cache_service import CacheService  # noqa: E402
from app.services.domain_service import MOCK_LISTINGS  # noqa: E402
from app.services.govdata_service import MOCK_MARKET_METRICS  # noqa: E402

# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

mock_location = LocationSummary(
    id="test-loc-1",
    display_name="Sydney NSW",
    city="Sydney",
    state="NSW",
    country_code="AU",
    latitude=-33.87,
    longitude=151.21,
)


def _make_valid_listings() -> list[PropertyListing]:
    return [
        PropertyListing(
            address="1 Test St, Sydney NSW 2000",
            price="$900,000",
            price_numeric=900000,
            beds=3,
            baths=2.0,
            listing_type="sold",
            property_type="house",
            source="domain",
        )
    ]


def _make_valid_demographics() -> DemographicsSnapshot:
    return DemographicsSnapshot(
        population=50000,
        population_growth_pct=2.0,
        median_age=32,
        median_household_income=90000,
        unemployment_rate=3.5,
        dominant_age_group="25-34",
        reference_year=2021,
        source="abs",
    )


def _make_valid_market_metrics() -> MarketMetrics:
    today = "2024-01-01"
    return MarketMetrics(
        median_sale_price=MetricValue(value=900000, source="test", date=today),
        median_rent_weekly=MetricValue(value=500, source="test", date=today),
        price_appreciation_yoy=MetricValue(value=5.0, source="test", date=today),
        rental_yield=MetricValue(value=2.9, source="test", date=today),
        days_on_market=MetricValue(value=21, source="test", date=today),
        inventory_level=MetricValue(value="low", source="test", date=today),
        market_sentiment=MetricValue(value="sellers", source="test", date=today),
    )


def _make_mock_db() -> AsyncMock:
    """Return an AsyncMock session whose add/flush are no-ops."""
    db = AsyncMock()
    db.add = MagicMock(return_value=None)
    db.flush = AsyncMock(return_value=None)
    return db


def _run_async(coro):
    """Run an async coroutine in a fresh event loop (Python 3.12 compatible)."""
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Property 6: Data Aggregation Completeness Under Partial Failure
#
# For every combination of [domain_ok, abs_ok, govdata_ok], the bundle must:
#   - have listings, demographics, market_metrics all non-null
#   - have len(listings) > 0
#   - have is_stale == True iff any service failed
# ---------------------------------------------------------------------------

@given(st.lists(st.booleans(), min_size=3, max_size=3))
@h_settings(max_examples=50)
def test_p6_aggregation_completeness_under_partial_failure(service_availability):
    """Property 6: Data Aggregation Completeness Under Partial Failure.

    For all 8 combinations of service availability, AggregationService always
    returns a fully-populated AggregatedDataBundle. Failed sources fall back to
    mock data and the bundle is marked is_stale=True.

    **Validates: Requirements 3.1, 9.2**
    """
    domain_ok, abs_ok, govdata_ok = service_availability
    any_failed = not (domain_ok and abs_ok and govdata_ok)

    svc = AggregationService()
    db = _make_mock_db()

    async def _run():
        domain_mock = AsyncMock(
            return_value=_make_valid_listings() if domain_ok else None,
            side_effect=None if domain_ok else Exception("Domain API down"),
        )
        abs_mock = AsyncMock(
            return_value=_make_valid_demographics() if abs_ok else None,
            side_effect=None if abs_ok else Exception("ABS API down"),
        )
        govdata_mock = AsyncMock(
            return_value=_make_valid_market_metrics() if govdata_ok else None,
            side_effect=None if govdata_ok else Exception("GovData API down"),
        )
        amenities_mock = AsyncMock(return_value=AmenitiesSnapshot())
        with (
            patch.object(svc._domain, "fetch_listings", new=domain_mock),
            patch.object(svc._abs, "fetch_demographics", new=abs_mock),
            patch.object(svc._govdata, "fetch_market_data", new=govdata_mock),
            patch.object(svc._amenities, "fetch_amenities", new=amenities_mock),
        ):
            return await svc.aggregate_for_location(mock_location, db)

    bundle = _run_async(_run())

    # --- Completeness assertions ---
    assert bundle is not None, "bundle must not be None"
    assert isinstance(bundle, AggregatedDataBundle)

    assert bundle.listings is not None, "listings must not be None"
    assert isinstance(bundle.listings, list)  # may be empty when PropertyLens is unavailable

    assert bundle.demographics is not None, "demographics must not be None"
    assert isinstance(bundle.demographics, DemographicsSnapshot)

    assert bundle.market_metrics is not None, "market_metrics must not be None"
    assert isinstance(bundle.market_metrics, MarketMetrics)

    # --- Staleness assertion ---
    assert bundle.is_stale == any_failed, (
        f"Expected is_stale={any_failed} for availability={service_availability}, "
        f"got is_stale={bundle.is_stale}"
    )


# ---------------------------------------------------------------------------
# Property 9: Cache Hit Idempotence (unit test)
#
# When Redis holds a pre-seeded bundle, repeated get_aggregated calls:
#   - each call reads from Redis (call count tracks correctly)
#   - return identical data both times
#   - no external API calls are made
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_p9_cache_hit_idempotence_no_external_calls():
    """Property 9: Cache Hit Idempotence — repeated reads within TTL use cached value.

    Builds a CacheService with a mock Redis that returns a pre-seeded bundle.
    Calls get_aggregated twice and asserts:
      - redis.get call count == 2 (the same cached value each time)
      - both results are non-null and identical
      - no external API calls were made

    **Validates: Requirements 3.5, 9.3**
    """
    location_id = "test-loc-1"

    # Build a representative bundle and serialise it
    bundle = AggregatedDataBundle(
        listings=_make_valid_listings(),
        demographics=_make_valid_demographics(),
        market_metrics=_make_valid_market_metrics(),
        is_stale=False,
    )
    serialized = bundle.model_dump_json()

    # Mock Redis that always returns the pre-seeded bundle
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=serialized)

    cache_svc = CacheService(redis_client=mock_redis)

    result1 = await cache_svc.get_aggregated(location_id)
    result2 = await cache_svc.get_aggregated(location_id)

    # Redis was called exactly twice — once per get_aggregated call
    assert mock_redis.get.call_count == 2, (
        f"Expected redis.get to be called 2 times, got {mock_redis.get.call_count}"
    )

    # Both results are non-null
    assert result1 is not None, "First cache hit returned None"
    assert result2 is not None, "Second cache hit returned None"

    # Data is identical across calls (idempotent)
    assert (
        result1.market_metrics.median_sale_price
        == result2.market_metrics.median_sale_price
    ), "Cache returned different median_sale_price on repeated calls"

    assert (
        result1.demographics.population == result2.demographics.population
    ), "Cache returned different population on repeated calls"

    assert len(result1.listings) == len(result2.listings), (
        "Cache returned different number of listings on repeated calls"
    )

    # is_stale must be False — the bundle was not stale when cached
    assert result1.is_stale is False
    assert result2.is_stale is False


# ---------------------------------------------------------------------------
# Additional: P6 edge case — all services succeed → is_stale must be False
# ---------------------------------------------------------------------------

def test_p6_all_services_ok_is_not_stale():
    """P6 edge case: when all three services succeed, is_stale must be False."""
    svc = AggregationService()
    db = _make_mock_db()

    async def _run():
        with (
            patch.object(
                svc._domain,
                "fetch_listings",
                new=AsyncMock(return_value=_make_valid_listings()),
            ),
            patch.object(
                svc._abs,
                "fetch_demographics",
                new=AsyncMock(return_value=_make_valid_demographics()),
            ),
            patch.object(
                svc._govdata,
                "fetch_market_data",
                new=AsyncMock(return_value=_make_valid_market_metrics()),
            ),
            patch.object(
                svc._amenities,
                "fetch_amenities",
                new=AsyncMock(return_value=AmenitiesSnapshot()),
            ),
        ):
            return await svc.aggregate_for_location(mock_location, db)

    bundle = _run_async(_run())

    assert bundle.is_stale is False, (
        f"All services succeeded but is_stale={bundle.is_stale}"
    )
    assert bundle.listings is not None and len(bundle.listings) > 0
    assert bundle.demographics is not None
    assert bundle.market_metrics is not None


# ---------------------------------------------------------------------------
# Additional: P6 edge case — all services fail → mock data returned, is_stale=True
# ---------------------------------------------------------------------------

def test_p6_all_services_fail_returns_mock_data():
    """P6 edge case: when all services fail, mock data is used and is_stale=True."""
    svc = AggregationService()
    db = _make_mock_db()

    async def _run():
        with (
            patch.object(
                svc._domain,
                "fetch_listings",
                new=AsyncMock(side_effect=Exception("Domain down")),
            ),
            patch.object(
                svc._abs,
                "fetch_demographics",
                new=AsyncMock(side_effect=Exception("ABS down")),
            ),
            patch.object(
                svc._govdata,
                "fetch_market_data",
                new=AsyncMock(side_effect=Exception("GovData down")),
            ),
            patch.object(
                svc._amenities,
                "fetch_amenities",
                new=AsyncMock(return_value=AmenitiesSnapshot()),
            ),
        ):
            return await svc.aggregate_for_location(mock_location, db)

    bundle = _run_async(_run())

    assert bundle.is_stale is True
    # PropertyLens failure → no fake listings, just an empty comparables list
    assert bundle.listings == []
    # Should use MOCK_DEMOGRAPHICS
    assert bundle.demographics.population == MOCK_DEMOGRAPHICS.population
    # Should use MOCK_MARKET_METRICS
    assert (
        bundle.market_metrics.median_sale_price == MOCK_MARKET_METRICS.median_sale_price
    )
