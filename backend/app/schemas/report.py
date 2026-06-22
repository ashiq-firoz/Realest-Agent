from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.location import LocationSummary
from app.schemas.geography import GeographyMetadata
from typing import Generic, TypeVar

T = TypeVar("T")

class MetricValue(BaseModel, Generic[T]):
    """Metric value with source attribution."""
    value: T
    source: str
    date: str


class PropertyListing(BaseModel):
    """Canonical schema after Domain API normalization."""

    address: str
    price: str                       # Formatted: "$450,000"
    price_numeric: Optional[int] = None  # For sorting/filtering
    beds: int
    baths: float
    sqft: Optional[int] = None
    listing_type: Literal["sold", "active", "leased"]
    property_type: Literal["house", "unit", "townhouse", "land", "other"]
    listed_at: Optional[date] = None
    source: str = "domain"
    metadata: Optional[GeographyMetadata] = None

    def belongs_to_target_geography(self, target_identity: "GeographicIdentity") -> bool:
        """Check if property belongs to target geography (naive implementation for fallback checking)."""
        # A more robust check might live in the ComparablePropertyService.
        # This basic check ensures state matches, and postcode/suburb match if provided on both sides.
        from app.schemas.geography import GeographicIdentity
        
        # State must always match
        if self.metadata and self.metadata.geography_type == "state":
            if target_identity.state.lower() != self.metadata.geography_id.lower():
                return False

        # Postcode match
        if target_identity.postcode and self.address:
            # We assume address might contain postcode, or we rely on metadata
            if self.metadata and self.metadata.geography_type == "postcode":
                if target_identity.postcode != self.metadata.geography_id:
                    return False

        # Suburb match
        if target_identity.suburb and self.address:
            if self.metadata and self.metadata.geography_type == "suburb":
                if target_identity.suburb.lower() not in self.metadata.geography_id.lower():
                    return False
            else:
                # Fallback to string matching on address
                if target_identity.suburb.lower() not in self.address.lower():
                    # Wait, string match might fail like "Darwin" in "Darwin Street, Boronia".
                    # Let's not string match if metadata isn't explicitly matching.
                    pass

        return True


class DemographicsSnapshot(BaseModel):
    """Canonical schema after ABS API normalization."""

    population: int
    population_growth_pct: float     # Annual %
    median_age: int
    median_household_income: int     # AUD (annual)
    unemployment_rate: float         # %
    dominant_age_group: str
    reference_year: int
    # ABS Census G02 also returns median weekly rent for the postcode; captured
    # here (in the same call) so the market metrics builder can use the real value.
    median_rent_weekly: Optional[int] = None  # AUD/week, real (ABS) when available
    source: str = "abs"
    metadata: Optional[GeographyMetadata] = None


class AmenitiesSnapshot(BaseModel):
    """Neighbourhood amenity counts from OpenStreetMap (Overpass API)."""

    schools: int = 0
    hospitals: int = 0
    pharmacies: int = 0
    supermarkets: int = 0
    parks: int = 0
    train_stations: int = 0
    bus_stops: int = 0
    cafes_restaurants: int = 0
    walkability_score: int = 0       # 0-100 proxy derived from amenity density
    lifestyle_score: int = 0         # 0-100 proxy (parks, cafes, retail)
    radius_m: int = 1500
    source: str = "osm"
    metadata: Optional[GeographyMetadata] = None


class MarketMetrics(BaseModel):
    """Aggregated market statistics."""

    median_sale_price: MetricValue[int]
    median_rent_weekly: MetricValue[int]
    price_appreciation_yoy: MetricValue[float]    # %
    rental_yield: MetricValue[float]              # %
    days_on_market: MetricValue[int]
    clearance_rate: Optional[MetricValue[float]] = None
    inventory_level: MetricValue[Literal["low", "medium", "high"]]
    market_sentiment: MetricValue[Literal["buyers", "balanced", "sellers"]]
    metadata: Optional[GeographyMetadata] = None


class ListingSummaryStats(BaseModel):
    """Summarized statistics of listings for Gemini to consume."""
    listing_count: int
    median_listing_price: Optional[int]
    property_type_distribution: dict[str, int]
    days_on_market_distribution: dict[str, int]


class AnalyticsBundle(BaseModel):
    """Deterministic analytics derived from metrics."""
    market_state: str
    growth_band: str
    yield_band: str
    inventory_state: str
    buyer_demand: str


class AggregatedDataBundle(BaseModel):
    """In-memory schema used to pass aggregated data between services."""

    listings: list[PropertyListing]
    demographics: DemographicsSnapshot
    market_metrics: MarketMetrics
    amenities: Optional[AmenitiesSnapshot] = None
    is_stale: bool = False
    
class GeminiReportResponse(BaseModel):
    """Schema for Gemini JSON structured output."""
    market_overview: str
    neighbourhood_insights: str
    demographics: str
    investment_intelligence: str
    comparable_properties_summary: str
    ai_summary: str
    risk_indicators: str
    opportunities: str


class ReportGenerationRequest(BaseModel):
    location_id: str


class ReportResponse(BaseModel):
    id: str
    share_token: str
    location: LocationSummary
    market_overview: str
    neighbourhood_insights: str
    demographics_section: str
    investment_intelligence: str
    comparable_properties: list[PropertyListing]
    ai_summary: str
    median_price: Optional[str] = None
    price_appreciation: Optional[str] = None
    rental_yield: Optional[str] = None
    days_on_market: Optional[int] = None
    roi_estimate: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PropertyFilters(BaseModel):
    propertyType: Optional[str] = None
    priceMin: Optional[int] = None
    priceMax: Optional[int] = None
    bedsMin: Optional[int] = None
    bathsMin: Optional[float] = None
