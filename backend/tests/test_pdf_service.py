"""
Property-based tests for PDFService.

**Property 15: PDF Content Completeness**
**Validates: Requirements 5.2**
"""
import os
import sys
from datetime import datetime
from io import BytesIO
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
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")

from app.schemas.location import LocationSummary  # noqa: E402
from app.schemas.report import PropertyListing, ReportResponse  # noqa: E402
from app.services.pdf_service import PDFService  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SECTION_HEADINGS = [
    "Market Overview",
    "Neighbourhood Insights",
    "Demographics",
    "Investment Intelligence",
    "Comparable Properties",
    "AI Summary",
]

BRAND_STRING = "Cotality"  # appears in the HTML as "CotalityIntelligence" across a span

FIXED_LOCATION = LocationSummary(
    id="loc-test-001",
    display_name="Sydney, NSW 2000",
    suburb="Sydney",
    city="Sydney",
    state="NSW",
    postcode="2000",
    country_code="AU",
    latitude=-33.8688,
    longitude=151.2093,
)

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_non_empty_text = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po", "Pd")),
    min_size=1,
    max_size=200,
).map(lambda s: s.strip() or "fallback content")

_property_listing_strategy = st.builds(
    PropertyListing,
    address=st.text(min_size=1, max_size=80).map(lambda s: s.strip() or "1 Test St"),
    price=st.integers(min_value=100_000, max_value=5_000_000).map(lambda n: f"${n:,}"),
    price_numeric=st.integers(min_value=100_000, max_value=5_000_000),
    beds=st.integers(min_value=1, max_value=6),
    baths=st.floats(min_value=1.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    sqft=st.one_of(st.none(), st.integers(min_value=40, max_value=500)),
    listing_type=st.sampled_from(["sold", "active", "leased"]),
    property_type=st.sampled_from(["house", "unit", "townhouse", "land", "other"]),
    listed_at=st.none(),
    source=st.just("domain"),
)


def report_response_strategy():
    """
    Composite Hypothesis strategy that generates valid ReportResponse fixtures
    with random IDs, section content, and 1-3 comparable properties.
    """
    return st.builds(
        ReportResponse,
        id=st.uuids().map(str),
        share_token=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            min_size=8,
            max_size=8,
        ),
        location=st.just(FIXED_LOCATION),
        market_overview=_non_empty_text,
        neighbourhood_insights=_non_empty_text,
        demographics_section=_non_empty_text,
        investment_intelligence=_non_empty_text,
        comparable_properties=st.lists(
            _property_listing_strategy, min_size=1, max_size=3
        ),
        ai_summary=_non_empty_text,
        median_price=st.one_of(st.none(), st.just("$1,200,000")),
        price_appreciation=st.one_of(st.none(), st.just("+5.2%")),
        rental_yield=st.one_of(st.none(), st.just("3.8%")),
        days_on_market=st.one_of(st.none(), st.integers(min_value=1, max_value=200)),
        roi_estimate=st.one_of(st.none(), st.just("7.1%")),
        created_at=st.just(datetime(2024, 6, 15, 10, 30, 0)),
    )


# ---------------------------------------------------------------------------
# Helper: render HTML from a ReportResponse (bypassing WeasyPrint)
# ---------------------------------------------------------------------------

def _render_html(service: PDFService, report: ReportResponse) -> str:
    """
    Invoke the Jinja2 rendering logic of PDFService directly, bypassing WeasyPrint.
    We patch weasyprint.HTML so generate() doesn't attempt PDF conversion,
    then capture the html_content that was passed.
    """
    captured: list[str] = []

    class CapturingHTML:
        def __init__(self, string: str, **_kwargs):
            captured.append(string)

        def write_pdf(self) -> bytes:
            return b"%PDF-1.4 fake"

    mock_wp = MagicMock()
    mock_wp.HTML = CapturingHTML
    with patch.dict("sys.modules", {"weasyprint": mock_wp}):
        service.generate(report)

    assert captured, "Expected weasyprint.HTML to be called with rendered HTML"
    return captured[0]


# ---------------------------------------------------------------------------
# Property 15: PDF Content Completeness
# **Validates: Requirements 5.2**
# ---------------------------------------------------------------------------

@given(report_response_strategy())
@settings(max_examples=50)
def test_p15_pdf_content_completeness(report: ReportResponse):
    """
    Property 15: For any valid ReportResponse, the rendered HTML output must contain:
    - The location display_name
    - The brand string "Cotality"
    - All 6 section headings (Market Overview, Neighbourhood Insights, Demographics,
      Investment Intelligence, Comparable Properties, AI Summary)
    - The created_at date string (formatted as day month year, e.g. "15 June 2024")

    **Validates: Requirements 5.2**
    """
    service = PDFService()
    html = _render_html(service, report)

    # 1. Location display_name must appear in the rendered HTML
    assert report.location.display_name in html, (
        f"Expected location display_name '{report.location.display_name}' in HTML output"
    )

    # 2. Brand string "Cotality" must appear
    assert BRAND_STRING in html, (
        f"Expected brand string '{BRAND_STRING}' in HTML output"
    )

    # 3. All 6 section headings must appear
    for heading in SECTION_HEADINGS:
        assert heading in html, (
            f"Expected section heading '{heading}' in HTML output"
        )

    # 4. created_at date string must appear (formatted as "15 June 2024")
    expected_date = report.created_at.strftime("%d %B %Y")
    assert expected_date in html, (
        f"Expected formatted date '{expected_date}' in HTML output"
    )


# ---------------------------------------------------------------------------
# Additional unit test: verify generate() returns bytes
# ---------------------------------------------------------------------------

def test_generate_returns_bytes():
    """
    Unit test: PDFService.generate() returns bytes when WeasyPrint is mocked.
    """
    service = PDFService()
    report = ReportResponse(
        id="test-id-001",
        share_token="ABCD1234",
        location=FIXED_LOCATION,
        market_overview="Strong market with increasing demand.",
        neighbourhood_insights="Quiet streets, excellent schools nearby.",
        demographics_section="Population of 50,000 with median age 35.",
        investment_intelligence="Rental yields are solid at 4.2%.",
        comparable_properties=[
            PropertyListing(
                address="10 George St, Sydney NSW 2000",
                price="$1,200,000",
                price_numeric=1_200_000,
                beds=3,
                baths=2.0,
                sqft=120,
                listing_type="sold",
                property_type="unit",
                source="domain",
            )
        ],
        ai_summary="This suburb presents a strong investment opportunity.",
        created_at=datetime(2024, 6, 15, 10, 30, 0),
    )

    mock_pdf_bytes = b"%PDF-1.4 mock content"

    mock_wp = MagicMock()
    mock_html_instance = MagicMock()
    mock_html_instance.write_pdf.return_value = mock_pdf_bytes
    mock_wp.HTML.return_value = mock_html_instance

    with patch.dict("sys.modules", {"weasyprint": mock_wp}):
        result = service.generate(report)

    assert isinstance(result, bytes), "generate() must return bytes"
    assert result == mock_pdf_bytes, "generate() must return the PDF bytes from WeasyPrint"


def test_generate_html_contains_all_required_content():
    """
    Unit test: The HTML passed to WeasyPrint contains all required content
    for a known ReportResponse.
    """
    service = PDFService()
    report = ReportResponse(
        id="test-id-002",
        share_token="XY789012",
        location=FIXED_LOCATION,
        market_overview="Market overview text here.",
        neighbourhood_insights="Neighbourhood insights text here.",
        demographics_section="Demographics text here.",
        investment_intelligence="Investment text here.",
        comparable_properties=[
            PropertyListing(
                address="5 Pitt St, Sydney NSW 2000",
                price="$950,000",
                price_numeric=950_000,
                beds=2,
                baths=1.0,
                sqft=80,
                listing_type="active",
                property_type="unit",
                source="domain",
            )
        ],
        ai_summary="AI summary text here.",
        created_at=datetime(2024, 6, 15, 10, 30, 0),
    )

    html = _render_html(service, report)

    assert "Sydney, NSW 2000" in html, "display_name must be in HTML"
    assert "Cotality" in html, "Brand must be in HTML"
    assert "15 June 2024" in html, "Formatted date must be in HTML"

    for heading in SECTION_HEADINGS:
        assert heading in html, f"Section heading '{heading}' must be in HTML"
