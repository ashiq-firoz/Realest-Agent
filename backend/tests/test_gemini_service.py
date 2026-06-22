"""
Property-based tests for GeminiService.

**Property 7: Gemini Response Section Parsing**
**Property 10: Partial Report on Gemini Failure**
**Property 24: Gemini Prompt Data Completeness**
**Validates: Requirements 3.3, 3.7, 11.1, 11.2**
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Set required env vars BEFORE importing any app module
# ---------------------------------------------------------------------------
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("NEXTAUTH_SECRET", "test_secret_min_32_characters_long_abc")
os.environ.setdefault("DOMAIN_API_KEY", "test")

# ---------------------------------------------------------------------------
# Stub out google.generativeai BEFORE importing GeminiService so that
# genai.configure() and genai.GenerativeModel() don't make real network calls.
# ---------------------------------------------------------------------------
genai_mock = MagicMock()
sys.modules.setdefault("google", MagicMock())
sys.modules.setdefault("google.generativeai", genai_mock)

from app.schemas.location import LocationSummary  # noqa: E402
from app.schemas.report import (  # noqa: E402
    AggregatedDataBundle,
    DemographicsSnapshot,
    MarketMetrics,
    MetricValue,
    PropertyListing,
)


def _mv(value_strategy):
    """Wrap a value strategy into a MetricValue strategy."""
    return st.builds(
        MetricValue,
        value=value_strategy,
        source=st.just("test"),
        date=st.just("2024-01-01"),
    )
from app.services.gemini_service import (  # noqa: E402
    AI_SUMMARY_PLACEHOLDER,
    REQUIRED_SECTIONS,
    GeminiService,
)

# ---------------------------------------------------------------------------
# Fixed test location
# ---------------------------------------------------------------------------
TEST_LOCATION = LocationSummary(
    id="loc-001",
    display_name="Bondi Beach, NSW 2026",
    suburb="Bondi Beach",
    city="Sydney",
    state="NSW",
    postcode="2026",
    country_code="AU",
    latitude=-33.8915,
    longitude=151.2767,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_full_response(sections: list[str]) -> str:
    """Build a Markdown response string with all listed section headers and content."""
    parts = []
    for section in sections:
        parts.append(f"## {section}\n\nSome meaningful content about {section}.\n")
    return "\n".join(parts)


def build_response_without(missing_section: str) -> str:
    """Build a Markdown response that is missing the given section."""
    present = [s for s in REQUIRED_SECTIONS if s != missing_section]
    return build_full_response(present)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

property_listing_strategy = st.builds(
    PropertyListing,
    address=st.text(min_size=1, max_size=100).map(lambda s: s.strip() or "1 Test St"),
    price=st.integers(min_value=100_000, max_value=10_000_000).map(lambda n: f"${n:,}"),
    price_numeric=st.integers(min_value=100_000, max_value=10_000_000),
    beds=st.integers(min_value=0, max_value=10),
    baths=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    sqft=st.one_of(st.none(), st.integers(min_value=20, max_value=2000)),
    listing_type=st.sampled_from(["sold", "active", "leased"]),
    property_type=st.sampled_from(["house", "unit", "townhouse", "land", "other"]),
    listed_at=st.none(),
    source=st.just("domain"),
)

demographics_strategy = st.builds(
    DemographicsSnapshot,
    population=st.integers(min_value=1_000, max_value=5_000_000),
    population_growth_pct=st.floats(min_value=-5.0, max_value=20.0, allow_nan=False, allow_infinity=False),
    median_age=st.integers(min_value=18, max_value=80),
    median_household_income=st.integers(min_value=20_000, max_value=500_000),
    unemployment_rate=st.floats(min_value=0.0, max_value=30.0, allow_nan=False, allow_infinity=False),
    dominant_age_group=st.sampled_from(["0-14", "15-24", "25-34", "35-44", "45-54", "55-64", "65+"]),
    reference_year=st.integers(min_value=2000, max_value=2030),
    source=st.just("abs"),
)

market_metrics_strategy = st.builds(
    MarketMetrics,
    median_sale_price=_mv(st.integers(min_value=100_000, max_value=10_000_000)),
    median_rent_weekly=_mv(st.integers(min_value=100, max_value=5_000)),
    price_appreciation_yoy=_mv(st.floats(min_value=-20.0, max_value=50.0, allow_nan=False, allow_infinity=False)),
    rental_yield=_mv(st.floats(min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False)),
    days_on_market=_mv(st.integers(min_value=1, max_value=365)),
    clearance_rate=st.one_of(
        st.none(),
        _mv(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
    ),
    inventory_level=_mv(st.sampled_from(["low", "medium", "high"])),
    market_sentiment=_mv(st.sampled_from(["buyers", "balanced", "sellers"])),
)


def aggregated_data_strategy():
    """Composite strategy that builds a valid AggregatedDataBundle."""
    return st.builds(
        AggregatedDataBundle,
        listings=st.lists(property_listing_strategy, min_size=1, max_size=5),
        demographics=demographics_strategy,
        market_metrics=market_metrics_strategy,
        is_stale=st.booleans(),
    )


# ---------------------------------------------------------------------------
# Property 7a: parse_sections — all 6 headers present → 6 non-empty keys
# ---------------------------------------------------------------------------

@given(st.sampled_from(REQUIRED_SECTIONS))
@settings(max_examples=50)
def test_p7a_parse_sections_all_headers_present(ignored_section):
    """Property 7a: When all 6 required headers are present, parse_sections returns
    all 6 keys with non-empty content.

    **Validates: Requirements 3.3, 11.1**
    """
    svc = GeminiService()
    response_text = build_full_response(REQUIRED_SECTIONS)

    result = svc.parse_sections(response_text)

    assert len(result) == 6, f"Expected 6 sections, got {len(result)}: {list(result.keys())}"
    for section in REQUIRED_SECTIONS:
        assert section in result, f"Section '{section}' missing from parsed result"
        assert result[section].strip(), f"Section '{section}' content is empty"


# ---------------------------------------------------------------------------
# Property 7b: parse_sections — one header absent → validate_sections reports it missing
# ---------------------------------------------------------------------------

@given(st.sampled_from(REQUIRED_SECTIONS))
@settings(max_examples=50)
def test_p7b_missing_section_reported_by_validate(missing_section):
    """Property 7b: When a required section header is absent from the response,
    validate_sections returns a non-empty list containing that section name.

    **Validates: Requirements 3.3, 11.1**
    """
    svc = GeminiService()
    response_text = build_response_without(missing_section)

    parsed = svc.parse_sections(response_text)
    missing = svc.validate_sections(parsed)

    assert len(missing) > 0, (
        f"validate_sections should report at least one missing section "
        f"when '{missing_section}' header is absent"
    )
    assert missing_section in missing, (
        f"validate_sections should report '{missing_section}' as missing, got: {missing}"
    )


# ---------------------------------------------------------------------------
# Property 24: build_prompt — JSON block contains all 3 data categories and
#              all 6 section names appear in the prompt
# ---------------------------------------------------------------------------

@given(aggregated_data_strategy())
@settings(max_examples=50)
def test_p24_build_prompt_data_completeness(data):
    """Property 24: build_prompt always produces a prompt that:
    - contains the three data categories (market_metrics, demographics, listings)
    - contains all 6 required section names

    **Validates: Requirements 3.7, 11.2**
    """
    svc = GeminiService()
    prompt = svc.build_prompt(TEST_LOCATION, data)

    # All three data categories must appear in the JSON block
    assert "market_metrics" in prompt, "Prompt must contain 'market_metrics' key in JSON block"
    assert "demographics" in prompt, "Prompt must contain 'demographics' key in JSON block"
    assert "listings" in prompt, "Prompt must contain 'listings' key in JSON block"

    # All 6 section names must appear in the prompt (as ## headers or instructions)
    for section in REQUIRED_SECTIONS:
        assert section in prompt, (
            f"Prompt must contain section name '{section}'"
        )


# ---------------------------------------------------------------------------
# Property 10: generate_report — on Gemini Exception → ai_summary is non-empty
# ---------------------------------------------------------------------------

@given(aggregated_data_strategy())
@settings(max_examples=30)
@pytest.mark.asyncio
async def test_p10_partial_report_on_gemini_failure(data):
    """Property 10: When genai raises an Exception during generate_content,
    generate_report returns a dict where 'AI Summary' is a non-empty placeholder string.

    **Validates: Requirements 3.3, 11.1, 11.2**
    """
    with patch("app.services.gemini_service.genai") as mock_genai:
        # Configure the patched genai so __init__ doesn't fail
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("Simulated Gemini API failure")
        mock_genai.GenerativeModel.return_value = mock_model

        svc = GeminiService()
        result = await svc.generate_report(TEST_LOCATION, data)

    # Must return a dict
    assert isinstance(result, dict), "generate_report must return a dict on failure"

    # AI Summary must be present and non-empty
    assert "AI Summary" in result, "Result dict must contain 'AI Summary' key"
    assert result["AI Summary"], "'AI Summary' must not be an empty string on failure"
    assert result["AI Summary"].strip(), "'AI Summary' must not be blank on failure"
