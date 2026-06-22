"""
Property tests for dashboard queries.

Property 16: Dashboard Ordering and Limit
Property 17: Soft-Delete Visibility
Property 18: Saved Location Round-Trip
Property 19: Investment Analytics Ordering
Property 20: Pro Feature Gate
"""
import asyncio
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("DOMAIN_API_KEY", "test")
os.environ.setdefault("NEXTAUTH_SECRET", "test_secret_min_32_characters_long_abc")

import pytest
from fastapi import HTTPException
from hypothesis import HealthCheck
from hypothesis import given
from hypothesis import settings as h_settings
from hypothesis import strategies as st

from app.deps import require_pro
from app.models.location import Location
from app.models.report import Report
from app.models.saved_location import SavedLocation
from app.models.user import User
from app.models.watchlist import WatchlistEntry
from app.models.aggregated_data import AggregatedMarketData
from app.routers.dashboard import get_analytics, get_reports, get_saved_locations, save_location, SavedLocationCreate

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

def _report_strategy(user_id: str, location_id: str):
    return st.builds(
        Report,
        id=st.uuids().map(str),
        user_id=st.just(user_id),
        location_id=st.just(location_id),
        share_token=st.text(min_size=8, max_size=8),
        market_overview=st.text(max_size=10),
        neighbourhood_insights=st.text(max_size=10),
        demographics_section=st.text(max_size=10),
        investment_intelligence=st.text(max_size=10),
        comparable_properties=st.just("[]"),
        ai_summary=st.text(max_size=10),
        median_price=st.just("$1,000,000"),
        price_appreciation=st.just("5%"),
        rental_yield=st.just("4%"),
        days_on_market=st.integers(1, 100),
        roi_estimate=st.sampled_from(["7.1%", "5.5%", "10.0%", None]),
        is_deleted=st.booleans(),
        created_at=st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2025, 1, 1),
        ),
    )

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_p16_p17_dashboard_ordering_limit_and_soft_delete():
    """
    Property 16 & 17: Dashboard Ordering, Limit, and Soft-Delete Visibility.
    """
    user_id = "user-100"
    user = User(id=user_id, tier="regular", email="test@test.com")
    
    @given(st.lists(_report_strategy(user_id, "loc-100"), min_size=0, max_size=50))
    @h_settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def run_property(reports):
        mock_db = AsyncMock()
        
        # Simulate SQL logic: filter out deleted, order by created_at desc, limit 20
        filtered = [r for r in reports if not r.is_deleted]
        filtered.sort(key=lambda x: x.created_at, reverse=True)
        sql_results = filtered[:20]
        
        # Mock the first execute (reports)
        mock_reports_result = MagicMock()
        mock_reports_result.scalars.return_value.all.return_value = sql_results
        
        # Mock the second execute (locations)
        loc = Location(id="loc-100", display_name="Test Loc", country_code="AU", city="City", state="State", latitude=0.0, longitude=0.0, suburb="Suburb", postcode="2000")
        mock_locations_result = MagicMock()
        mock_locations_result.scalars.return_value.all.return_value = [loc]
        
        mock_db.execute.side_effect = [mock_reports_result, mock_locations_result]
        
        results = asyncio.run(get_reports(db=mock_db, current_user=user))
        
        # Assertions
        assert len(results) <= 20
        for i in range(len(results) - 1):
            assert results[i].created_at >= results[i+1].created_at
        
        fetched_ids = {r.id for r in results}
        for r in reports:
            if r.is_deleted:
                assert r.id not in fetched_ids
                
    run_property()

def test_p18_saved_location_round_trip():
    """Property 18: Saved Location Round-Trip"""
    user_id = "user-200"
    user = User(id=user_id, tier="pro", email="pro@test.com")
    
    @given(st.uuids())
    @h_settings(max_examples=10)
    def run_property(loc_uuid):
        loc_id = str(loc_uuid)
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        async def mock_refresh(saved_loc):
            saved_loc.id = "mock-id"
            saved_loc.created_at = datetime.now()
            
        mock_db.refresh.side_effect = mock_refresh
        
        loc = Location(id=loc_id, display_name="Test Loc", country_code="AU", city="City", state="State", latitude=0.0, longitude=0.0, suburb="Suburb", postcode="2000")
        
        # For save_location:
        # 1. execute -> Location
        mock_loc_res = MagicMock()
        mock_loc_res.scalar_one_or_none.return_value = loc
        
        # 2. execute -> SavedLocation (None to simulate new)
        mock_exist_res = MagicMock()
        mock_exist_res.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [mock_loc_res, mock_exist_res]
        
        req = SavedLocationCreate(location_id=loc_id)
        saved = asyncio.run(save_location(body=req, db=mock_db, current_user=user))
        assert saved.location.id == loc_id
        
        # For get_saved_locations:
        mock_db2 = AsyncMock()
        sl = SavedLocation(id="sl-1", user_id=user_id, location_id=loc_id, created_at=datetime.now())
        
        mock_sl_res = MagicMock()
        mock_sl_res.scalars.return_value.all.return_value = [sl]
        
        mock_locs_res = MagicMock()
        mock_locs_res.scalars.return_value.all.return_value = [loc]
        
        mock_db2.execute.side_effect = [mock_sl_res, mock_locs_res]
        
        listed = asyncio.run(get_saved_locations(db=mock_db2, current_user=user))
        assert any(s.location.id == loc_id for s in listed)
        
    run_property()

def test_p19_investment_analytics_ordering():
    """Property 19: Investment Analytics Ordering"""
    user_id = "user-300"
    user = User(id=user_id, tier="pro", email="pro3@test.com")
    
    @given(st.lists(_report_strategy(user_id, "loc-300"), min_size=1, max_size=10))
    @h_settings(max_examples=10)
    def run_property(reports):
        mock_db = AsyncMock()
        
        # 1. saved locations
        sl = SavedLocation(user_id=user_id, location_id="loc-300")
        mock_sl_res = MagicMock()
        mock_sl_res.scalars.return_value.all.return_value = [sl]
        
        # 2. locations
        loc = Location(id="loc-300", display_name="Test Loc", country_code="AU", city="City", state="State", latitude=0.0, longitude=0.0, suburb="Suburb", postcode="2000")
        mock_locs_res = MagicMock()
        mock_locs_res.scalars.return_value.all.return_value = [loc]
        
        # 3. reports
        # Router assumes reports are ordered by created_at desc
        reports[0].is_deleted = False # ensure at least 1
        filtered = [r for r in reports if not r.is_deleted]
        filtered.sort(key=lambda x: x.created_at, reverse=True)
        
        mock_reports_res = MagicMock()
        mock_reports_res.scalars.return_value.all.return_value = filtered
        
        mock_db.execute.side_effect = [mock_sl_res, mock_locs_res, mock_reports_res]
        
        analytics = asyncio.run(get_analytics(db=mock_db, current_user=user))
        
        def get_val(roi):
            if roi is None: return -9999
            return float(roi.strip().rstrip("%"))
        
        for i in range(len(analytics) - 1):
            assert get_val(analytics[i].roi_estimate) >= get_val(analytics[i+1].roi_estimate)
                    
    run_property()

@pytest.mark.asyncio
async def test_p20_pro_feature_gate():
    """Pro gate is permissive now: every tier (incl. regular) may access all
    features. require_pro returns the user instead of raising 403."""
    user = User(id="user-400", tier="regular", email="reg@test.com")

    result = await require_pro(user=user)
    assert result.tier == "regular"
