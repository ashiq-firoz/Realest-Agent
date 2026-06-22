"""
Property-based tests for GeoService.

Property 1: Autocomplete Results Are Bounded and Australian
Property 2: Location Resolution Completeness
Validates: Requirements 1.1, 1.2, 1.4
"""
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Set required env vars before importing app modules
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("NEXTAUTH_SECRET", "test_secret_min_32_characters_long_abc")
os.environ.setdefault("DOMAIN_API_KEY", "test")

from app.schemas.location import LocationSummary
from app.services.geo_service import GeoService

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Optional text value — either None or a short non-empty string
optional_text = st.one_of(st.none(), st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z"))))

# Required text — always a non-empty string
required_text = st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")))

# A strategy for a Nominatim address sub-dict with varied shapes.
# Some address keys may be absent entirely (hence the optional values).
address_strategy = st.fixed_dictionaries(
    {},
    optional={
        "suburb": optional_text,
        "city_district": optional_text,
        "city": optional_text,
        "town": optional_text,
        "village": optional_text,
        "municipality": optional_text,
        "county": optional_text,
        "state": optional_text,
        "state_district": optional_text,
        "postcode": optional_text,
        "country_code": st.one_of(st.none(), st.sampled_from(["au", "AU", "us", "gb", "nz", "de"])),
    },
)

# Strategy for a full Nominatim result dict (top-level fields plus address)
nominatim_result_strategy = st.fixed_dictionaries(
    {},
    optional={
        "place_id": st.one_of(st.none(), st.integers(min_value=1, max_value=10_000_000).map(str)),
        "display_name": optional_text,
        "lat": st.one_of(st.none(), st.floats(min_value=-90, max_value=90).map(str)),
        "lon": st.one_of(st.none(), st.floats(min_value=-180, max_value=180).map(str)),
        "importance": st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0)),
        "address": address_strategy,
    },
)

# Strategy for a Nominatim result that is guaranteed to be Australian
# (address.country_code in {"au", "AU"})
nominatim_au_result_strategy = st.fixed_dictionaries(
    {},
    optional={
        "place_id": st.integers(min_value=1, max_value=10_000_000).map(str),
        "display_name": required_text,
        "lat": st.floats(min_value=-44, max_value=-10).map(str),
        "lon": st.floats(min_value=112, max_value=154).map(str),
        "importance": st.floats(min_value=0.0, max_value=1.0),
        "address": st.fixed_dictionaries(
            {"country_code": st.sampled_from(["au", "AU"])},
            optional={
                "suburb": optional_text,
                "city_district": optional_text,
                "city": optional_text,
                "town": optional_text,
                "state": optional_text,
                "postcode": optional_text,
            },
        ),
    },
)

# Strategy for Nominatim results with varied country codes (for P1a mock)
country_code_strategy = st.sampled_from(["au", "AU", "us", "US", "gb", "GB", "nz", "NZ", "de", "DE"])

nominatim_result_with_country_strategy = st.fixed_dictionaries(
    {},
    optional={
        "place_id": st.integers(min_value=1, max_value=10_000_000).map(str),
        "display_name": required_text,
        "lat": st.floats(min_value=-90, max_value=90).map(str),
        "lon": st.floats(min_value=-180, max_value=180).map(str),
        "importance": st.floats(min_value=0.0, max_value=1.0),
        "address": st.fixed_dictionaries(
            {"country_code": country_code_strategy},
            optional={
                "suburb": optional_text,
                "city": optional_text,
                "state": optional_text,
            },
        ),
    },
)


# ---------------------------------------------------------------------------
# Property 2: Location Resolution Completeness
# parse_nominatim_result always returns a LocationSummary with all required
# fields non-null / non-empty.
# ---------------------------------------------------------------------------

@given(nominatim_result_strategy)
@settings(max_examples=100)
def test_p2_parse_nominatim_result_required_fields_non_null(result: dict) -> None:
    """
    **Validates: Requirements 1.2**

    Property 2: For any Nominatim result dict (including sparse/missing fields),
    parse_nominatim_result must return a LocationSummary where all *required*
    fields (id, display_name, city, state, country_code, latitude, longitude)
    are non-null and non-empty.
    Optional fields (suburb, postcode) may be None.
    """
    svc = GeoService()
    loc = svc.parse_nominatim_result(result)

    # Must return a LocationSummary
    assert isinstance(loc, LocationSummary)

    # Required fields must be non-null and non-empty
    assert loc.id is not None and loc.id != ""
    assert loc.display_name is not None and loc.display_name != ""
    assert loc.city is not None and loc.city != ""
    assert loc.state is not None and loc.state != ""
    assert loc.country_code is not None and loc.country_code != ""

    # latitude and longitude must be finite floats
    assert isinstance(loc.latitude, float)
    assert isinstance(loc.longitude, float)
    import math
    assert not math.isnan(loc.latitude)
    assert not math.isnan(loc.longitude)

    # country_code must be uppercase
    assert loc.country_code == loc.country_code.upper()


# ---------------------------------------------------------------------------
# Property 1b: is_australian correctness
# is_australian returns True iff country_code.upper() == "AU"
# ---------------------------------------------------------------------------

ALL_COUNTRY_CODES = ["AU", "US", "GB", "NZ", "DE", "FR", "JP", "CA", "IN", "CN",
                     "au", "us", "gb", "nz", "de", "fr", "jp", "ca", "in", "cn"]


@given(country_code=st.sampled_from(ALL_COUNTRY_CODES))
@settings(max_examples=100)
def test_p1b_is_australian_iff_country_code_au(country_code: str) -> None:
    """
    **Validates: Requirements 1.4**

    Property 1b: is_australian(loc) is True if and only if
    loc.country_code.upper() == "AU".
    """
    svc = GeoService()
    # Build a minimal LocationSummary with the given country_code
    loc = LocationSummary(
        id="test-id",
        display_name="Sydney, NSW",
        suburb=None,
        city="Sydney",
        state="NSW",
        postcode="2000",
        country_code=country_code,
        latitude=-33.8688,
        longitude=151.2093,
    )

    result = svc.is_australian(loc)
    expected = country_code.upper() == "AU"
    assert result == expected, (
        f"is_australian({country_code!r}) returned {result}, expected {expected}"
    )


# ---------------------------------------------------------------------------
# Property 1a: Autocomplete Results Are Bounded and Australian
# Mock httpx; assert output length ≤ 8 and all entries have country_code == "AU"
# ---------------------------------------------------------------------------

def _build_mock_nominatim_response(results: list[dict]) -> MagicMock:
    """Build a mock httpx Response that returns `results` as JSON."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value=results)
    return mock_resp


@given(
    raw_results=st.lists(
        nominatim_result_with_country_strategy,
        min_size=0,
        max_size=20,
    )
)
@settings(max_examples=50)
@pytest.mark.asyncio
async def test_p1a_autocomplete_bounded_and_australian(raw_results: list[dict]) -> None:
    """
    **Validates: Requirements 1.1, 1.2**

    Property 1a: autocomplete() must return:
    - At most 8 results
    - Only results where country_code == "AU"

    Even when Nominatim returns up to 20 mixed-country results.
    """
    svc = GeoService()
    mock_resp = _build_mock_nominatim_response(raw_results)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.geo_service.httpx.AsyncClient", return_value=mock_client):
        locations = await svc.autocomplete("Sydney")

    # P1a assertion 1: output bounded to at most 8
    assert len(locations) <= 8, (
        f"autocomplete returned {len(locations)} results, expected ≤ 8"
    )

    # P1a assertion 2: all returned entries are Australian
    for loc in locations:
        assert loc.country_code == "AU", (
            f"Non-Australian result returned: country_code={loc.country_code!r}"
        )


# ---------------------------------------------------------------------------
# Additional: autocomplete raises GeocodeError on HTTP failure
# (unit test, not property-based, but validates Requirement 1.1)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_autocomplete_raises_geocode_error_on_http_failure() -> None:
    """autocomplete() raises GeocodeError when Nominatim is unavailable."""
    import httpx
    from app.services.geo_service import GeocodeError

    svc = GeoService()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.HTTPError("Connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    # Use a query that does NOT match the local suburb dataset so autocomplete
    # falls through to Nominatim (which is mocked to fail) and raises GeocodeError.
    with patch("app.services.geo_service.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(GeocodeError):
            await svc.autocomplete("Zzqxboroughville")
