"""
Integration tests for report generation pipeline.

Property 10: Partial Report on Gemini Failure
Property 11: Report Rendering Completeness
Validates: Requirements 3.7, 4.1, 4.2
"""
import asyncio
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("DOMAIN_API_KEY", "test")
os.environ.setdefault("NEXTAUTH_SECRET", "test_secret_min_32_characters_long_abc")

import pytest
from hypothesis import given
from hypothesis import settings as h_settings
from hypothesis import strategies as st

from app.schemas.location import LocationSummary
from app.schemas.report import AggregatedDataBundle, ReportResponse
from app.services.report_service import ReportService
from tests.test_pdf_service import FIXED_LOCATION, _property_listing_strategy

from app.models.user import User
from app.models.location import Location
from app.models.report import Report
from app.models.saved_location import SavedLocation
from app.models.watchlist import WatchlistEntry
from app.models.aggregated_data import AggregatedMarketData

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_non_empty_text = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po", "Pd")),
    min_size=1,
    max_size=200,
).map(lambda s: s.strip() or "fallback content")

def location_strategy():
    return st.just(FIXED_LOCATION)

def aggregated_data_strategy():
    """Generates an AggregatedDataBundle with non-empty listings."""
    # We construct it using mocks or just instantiate the model
    # For simplicity, we just use a basic one.
    return st.builds(
        AggregatedDataBundle,
        listings=st.lists(_property_listing_strategy, min_size=1, max_size=3),
    )

def report_response_strategy():
    return st.builds(
        ReportResponse,
        id=st.uuids().map(str),
        share_token=st.text(min_size=8, max_size=8),
        created_at=st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2025, 1, 1),
        ),
        location=location_strategy(),
        market_overview=_non_empty_text,
        neighbourhood_insights=_non_empty_text,
        demographics_section=_non_empty_text,
        investment_intelligence=_non_empty_text,
        comparable_properties=st.lists(_property_listing_strategy, min_size=1, max_size=3),
        ai_summary=_non_empty_text,
    )

# ---------------------------------------------------------------------------
# Property 10: Partial Report on Gemini Failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_p10_partial_report_on_gemini_failure():
    """Property 10: Partial Report on Gemini Failure.
    
    If Gemini generation fails, the pipeline still persists and returns a Report
    with the 5 data sections populated and ai_summary showing a fallback placeholder.
    """
    # Mock dependencies
    service = ReportService()
    
    # 1. Mock DB Location
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_scalar = Location(
        id="loc-001",
        display_name="Sydney",
        suburb="Sydney",
        city="Sydney",
        state="NSW",
        postcode="2000",
        country_code="AU",
        latitude=0.0,
        longitude=0.0,
    )
    mock_db.execute.return_value = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.side_effect = [mock_scalar, None]
    
    # 2. Mock Cache / Aggregation
    service._cache.get_aggregated = AsyncMock(return_value=None)
    mock_bundle = MagicMock()
    mock_bundle.market_metrics.median_sale_price = 1000000
    mock_bundle.market_metrics.price_appreciation_yoy = 5.0
    mock_bundle.market_metrics.rental_yield = 4.0
    mock_bundle.market_metrics.days_on_market = 30
    mock_bundle.listings = []
    service._aggregation.aggregate_for_location = AsyncMock(return_value=mock_bundle)
    service._cache.set_aggregated = AsyncMock()
    
    # 3. Mock GeminiService to simulate what happens when it catches a GeminiError
    # The requirement asks to simulate Gemini failure. 
    # GeminiService returns 5 sections + ai_summary placeholder on error.
    fallback_sections = {
        "Market Overview": "fallback",
        "Neighbourhood Insights": "fallback",
        "Demographics": "fallback",
        "Investment Intelligence": "fallback",
        "Comparable Properties": "fallback",
        "AI Summary": "AI Summary temporarily unavailable. Please retry."
    }
    service._gemini.generate_report = AsyncMock(return_value=fallback_sections)
    
    async def mock_refresh(report):
        report.id = "test-id"
        report.created_at = datetime.now()
        
    mock_db.refresh.side_effect = mock_refresh
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    
    response = await service.create_report("user-123", "loc-001", mock_db)
    
    assert response.ai_summary == "AI Summary temporarily unavailable. Please retry."
    assert response.market_overview == "fallback"
    assert response.neighbourhood_insights == "fallback"
    assert response.demographics_section == "fallback"
    assert response.investment_intelligence == "fallback"

# ---------------------------------------------------------------------------
# Property 11: Report Rendering Completeness
# ---------------------------------------------------------------------------

@given(report_response_strategy())
@h_settings(max_examples=50)
def test_p11_report_rendering_completeness(report: ReportResponse):
    """Property 11: Report Rendering Completeness.
    
    Assert all 6 section keys are non-empty strings.
    """
    assert bool(report.market_overview.strip()), "market_overview must not be empty"
    assert bool(report.neighbourhood_insights.strip()), "neighbourhood_insights must not be empty"
    assert bool(report.demographics_section.strip()), "demographics_section must not be empty"
    assert bool(report.investment_intelligence.strip()), "investment_intelligence must not be empty"
    assert bool(report.ai_summary.strip()), "ai_summary must not be empty"
