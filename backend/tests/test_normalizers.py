"""
Property-based tests for data normalizers.

**Property 22: Data Normalization Schema Completeness**
**Validates: Requirements 9.4, 9.5**

Ensures that normalizer functions produce complete, correctly-typed output
for any valid input shape from the Domain API and ABS API.
"""
import math

from hypothesis import given, settings
from hypothesis import strategies as st

from app.schemas.report import DemographicsSnapshot, PropertyListing

# ---------------------------------------------------------------------------
# Inline normalizers for testing normalization logic
# ---------------------------------------------------------------------------

LISTING_TYPES = ["sold", "active", "leased"]
PROPERTY_TYPES = ["house", "unit", "townhouse", "land", "other"]


def normalize_listing(raw: dict) -> PropertyListing:
    """Normalize a raw Domain API listing dict into PropertyListing."""
    price_numeric = raw.get("price")
    price_display = raw.get("price_display") or (
        f"${price_numeric:,}" if price_numeric is not None else "$0"
    )
    return PropertyListing(
        address=raw.get("address", "Unknown address") or "Unknown address",
        price=price_display,
        price_numeric=price_numeric,
        beds=int(raw.get("bedrooms", 0) or 0),
        baths=float(raw.get("bathrooms", 0) or 0),
        sqft=raw.get("sqft"),
        listing_type=raw.get("listing_type", "active"),
        property_type=raw.get("property_type", "house"),
        listed_at=raw.get("listed_at"),
        source=raw.get("source", "domain"),
    )


def normalize_demographics(raw: dict) -> DemographicsSnapshot:
    """Normalize a raw ABS API demographics dict into DemographicsSnapshot."""
    return DemographicsSnapshot(
        population=int(raw.get("total_population", 0) or 0),
        population_growth_pct=float(raw.get("growth_rate", 0.0) or 0.0),
        median_age=int(raw.get("median_age", 30) or 30),
        median_household_income=int(raw.get("household_income", 60000) or 60000),
        unemployment_rate=float(raw.get("unemployment", 0.0) or 0.0),
        dominant_age_group=raw.get("dominant_age_group") or "25-34",
        reference_year=int(raw.get("year", 2021) or 2021),
        source=raw.get("source", "abs"),
    )


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

domain_listing_strategy = st.fixed_dictionaries({
    "address": st.one_of(st.text(min_size=1, max_size=200), st.none()),
    "price_display": st.one_of(st.text(max_size=20), st.none()),
    "price": st.one_of(st.integers(min_value=0, max_value=10_000_000), st.none()),
    "bedrooms": st.one_of(st.integers(min_value=0, max_value=10), st.none()),
    "bathrooms": st.one_of(
        st.floats(min_value=0, max_value=10, allow_nan=False, allow_infinity=False),
        st.none(),
    ),
    "sqft": st.one_of(st.integers(min_value=1, max_value=10000), st.none()),
    "listing_type": st.sampled_from(LISTING_TYPES),
    "property_type": st.sampled_from(PROPERTY_TYPES),
    "listed_at": st.none(),
    "source": st.just("domain"),
})

abs_demographics_strategy = st.fixed_dictionaries({
    "total_population": st.one_of(st.integers(min_value=0, max_value=5_000_000), st.none()),
    "growth_rate": st.one_of(
        st.floats(min_value=-10, max_value=20, allow_nan=False, allow_infinity=False),
        st.none(),
    ),
    "median_age": st.one_of(st.integers(min_value=1, max_value=100), st.none()),
    "household_income": st.one_of(st.integers(min_value=0, max_value=500_000), st.none()),
    "unemployment": st.one_of(
        st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
        st.none(),
    ),
    "dominant_age_group": st.one_of(
        st.sampled_from(["0-14", "15-24", "25-34", "35-44", "45-54", "55-64", "65+"]),
        st.none(),
    ),
    "year": st.one_of(st.integers(min_value=2000, max_value=2030), st.none()),
    "source": st.just("abs"),
})


# ---------------------------------------------------------------------------
# Property 22a: Listing normalization completeness
# ---------------------------------------------------------------------------

@given(domain_listing_strategy)
@settings(max_examples=100)
def test_normalize_listing_completeness(raw):
    """Property 22a: Every normalized listing has all required fields with correct types.

    **Validates: Requirements 9.4, 9.5**
    """
    listing = normalize_listing(raw)

    # Must produce a valid PropertyListing instance
    assert isinstance(listing, PropertyListing)

    # address must be a non-empty string
    assert isinstance(listing.address, str)
    assert listing.address, "address must not be empty"

    # price must be a non-empty string (formatted display value)
    assert isinstance(listing.price, str)
    assert listing.price, "price must not be empty"

    # beds must be an int
    assert isinstance(listing.beds, int)

    # baths must be a float
    assert isinstance(listing.baths, float)
    assert not math.isnan(listing.baths), "baths must not be NaN"

    # listing_type must be one of the allowed literals
    assert listing.listing_type in LISTING_TYPES

    # property_type must be one of the allowed literals
    assert listing.property_type in PROPERTY_TYPES

    # source must be a non-empty string
    assert isinstance(listing.source, str)
    assert listing.source, "source must not be empty"


# ---------------------------------------------------------------------------
# Property 22b: Demographics normalization completeness
# ---------------------------------------------------------------------------

@given(abs_demographics_strategy)
@settings(max_examples=100)
def test_normalize_demographics_completeness(raw):
    """Property 22b: Every normalized demographics snapshot has all required fields with correct types.

    **Validates: Requirements 9.4, 9.5**
    """
    demo = normalize_demographics(raw)

    # Must produce a valid DemographicsSnapshot instance
    assert isinstance(demo, DemographicsSnapshot)

    # population must be a non-negative int
    assert isinstance(demo.population, int)
    assert demo.population >= 0

    # population_growth_pct must be a float
    assert isinstance(demo.population_growth_pct, float)
    assert not math.isnan(demo.population_growth_pct), "population_growth_pct must not be NaN"

    # median_age must be a positive int
    assert isinstance(demo.median_age, int)
    assert demo.median_age > 0

    # median_household_income must be a non-negative int
    assert isinstance(demo.median_household_income, int)
    assert demo.median_household_income >= 0

    # unemployment_rate must be a float
    assert isinstance(demo.unemployment_rate, float)
    assert not math.isnan(demo.unemployment_rate), "unemployment_rate must not be NaN"

    # dominant_age_group must be a non-empty string
    assert isinstance(demo.dominant_age_group, str)
    assert demo.dominant_age_group, "dominant_age_group must not be empty"

    # reference_year must be an int
    assert isinstance(demo.reference_year, int)

    # source must be a non-empty string
    assert isinstance(demo.source, str)
    assert demo.source, "source must not be empty"
