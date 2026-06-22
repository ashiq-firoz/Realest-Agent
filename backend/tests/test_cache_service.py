"""
Property-based tests for CacheService.

Property 9: Cache Hit Idempotence
Validates: Requirements 3.5, 9.3
"""
import json
import os
from unittest.mock import AsyncMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Set required env vars before importing app modules
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GEMINI_API_KEY", "test_key")
os.environ.setdefault("NEXTAUTH_SECRET", "test_secret_min_32_characters_long_abc")
os.environ.setdefault("DOMAIN_API_KEY", "test_domain_key")

from app.schemas.report import (
    AggregatedDataBundle,
    DemographicsSnapshot,
    MarketMetrics,
    MetricValue,
    PropertyListing,
)
from app.services.cache_service import CacheService

_T = "2024-01-01"


def make_bundle(median_price: int = 750000, population: int = 45000) -> AggregatedDataBundle:
    return AggregatedDataBundle(
        listings=[
            PropertyListing(
                address="1 Test St",
                price=f"${median_price:,}",
                price_numeric=median_price,
                beds=3,
                baths=2.0,
                listing_type="sold",
                property_type="house",
                source="mock",
            )
        ],
        demographics=DemographicsSnapshot(
            population=population,
            population_growth_pct=1.5,
            median_age=35,
            median_household_income=80000,
            unemployment_rate=4.0,
            dominant_age_group="25-34",
            reference_year=2021,
            source="mock",
        ),
        market_metrics=MarketMetrics(
            median_sale_price=MetricValue(value=median_price, source="mock", date=_T),
            median_rent_weekly=MetricValue(value=450, source="mock", date=_T),
            price_appreciation_yoy=MetricValue(value=4.5, source="mock", date=_T),
            rental_yield=MetricValue(value=3.3, source="mock", date=_T),
            days_on_market=MetricValue(value=28, source="mock", date=_T),
            inventory_level=MetricValue(value="medium", source="mock", date=_T),
            market_sentiment=MetricValue(value="balanced", source="mock", date=_T),
        ),
        is_stale=False,
    )


@given(
    location_id=st.uuids().map(str),
    median_price=st.integers(min_value=100_000, max_value=5_000_000),
    population=st.integers(min_value=1_000, max_value=5_000_000),
)
@settings(max_examples=50)
@pytest.mark.asyncio
async def test_cache_aggregated_round_trip(location_id, median_price, population):
    """Property 9a: Data stored via set_aggregated is returned intact by get_aggregated."""
    store: dict[str, str] = {}

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(side_effect=lambda key: store.get(key))
    mock_redis.set = AsyncMock(
        side_effect=lambda key, value, ex=None: store.update({key: value}) or None
    )

    svc = CacheService(redis_client=mock_redis)
    bundle = make_bundle(median_price=median_price, population=population)

    await svc.set_aggregated(location_id, bundle)
    result = await svc.get_aggregated(location_id)

    assert result is not None
    assert result.market_metrics.median_sale_price == bundle.market_metrics.median_sale_price
    assert result.demographics.population == bundle.demographics.population
    assert len(result.listings) == len(bundle.listings)
    assert result.listings[0].address == bundle.listings[0].address


@given(location_id=st.uuids().map(str))
@settings(max_examples=50)
@pytest.mark.asyncio
async def test_cache_miss_returns_none(location_id):
    """Property 9b: get_aggregated returns None when the key does not exist."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)

    svc = CacheService(redis_client=mock_redis)
    result = await svc.get_aggregated(location_id)

    assert result is None


@given(location_id=st.uuids().map(str))
@settings(max_examples=50)
@pytest.mark.asyncio
async def test_cache_invalidate_removes_key(location_id):
    """Property 9c: After invalidate, get_aggregated returns None."""
    store: dict[str, str] = {}
    bundle = make_bundle()

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(side_effect=lambda key: store.get(key))
    mock_redis.set = AsyncMock(
        side_effect=lambda key, value, ex=None: store.update({key: value}) or None
    )
    mock_redis.delete = AsyncMock(side_effect=lambda key: store.pop(key, None))

    svc = CacheService(redis_client=mock_redis)
    await svc.set_aggregated(location_id, bundle)
    await svc.invalidate(location_id)
    result = await svc.get_aggregated(location_id)

    assert result is None


@pytest.mark.asyncio
async def test_no_external_calls_on_cache_hit():
    """Property 9d: Repeated get_aggregated calls use cached value idempotently."""
    location_id = "test-location-123"
    bundle = make_bundle()
    serialized = bundle.model_dump_json()

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=serialized)

    svc = CacheService(redis_client=mock_redis)

    result1 = await svc.get_aggregated(location_id)
    result2 = await svc.get_aggregated(location_id)

    assert mock_redis.get.call_count == 2
    assert result1 is not None
    assert result2 is not None
    assert result1.market_metrics.median_sale_price == result2.market_metrics.median_sale_price
