/**
 * TypeScript interfaces matching all Pydantic response schemas from the FastAPI backend.
 * Keep this file in sync with backend/app/schemas/.
 */

export interface LocationSummary {
  id: string;
  display_name: string;
  suburb?: string;
  city: string;
  state: string;
  postcode?: string;
  country_code: string;
  latitude: number;
  longitude: number;
}

export interface PropertyListing {
  address: string;
  /** Formatted price string, e.g. "$450,000" */
  price: string;
  /** Numeric price for sorting/filtering */
  price_numeric?: number;
  beds: number;
  baths: number;
  sqft?: number;
  listing_type: "sold" | "active" | "leased";
  property_type: "house" | "unit" | "townhouse" | "land" | "other";
  listed_at?: string;
  source: string;
}

export interface DemographicsSnapshot {
  population: number;
  /** Annual growth percentage */
  population_growth_pct: number;
  median_age: number;
  /** Median household income in AUD */
  median_household_income: number;
  /** Unemployment rate as a percentage */
  unemployment_rate: number;
  dominant_age_group: string;
  reference_year: number;
  source: string;
}

export interface MarketMetrics {
  median_sale_price: number;
  median_rent_weekly: number;
  /** Year-over-year price appreciation as a percentage */
  price_appreciation_yoy: number;
  /** Rental yield as a percentage */
  rental_yield: number;
  days_on_market: number;
  clearance_rate?: number;
  inventory_level: "low" | "medium" | "high";
  market_sentiment: "buyers" | "balanced" | "sellers";
}

export interface ReportResponse {
  id: string;
  share_token: string;
  location: LocationSummary;
  market_overview: string;
  neighbourhood_insights: string;
  demographics_section: string;
  investment_intelligence: string;
  comparable_properties: PropertyListing[];
  ai_summary: string;
  median_price?: string;
  price_appreciation?: string;
  rental_yield?: string;
  days_on_market?: number;
  roi_estimate?: string;
  user_id?: string;
  created_at: string;
}

export interface PropertyFilters {
  propertyType?: "house" | "unit" | "townhouse" | "land" | "other";
  priceMin?: number;
  priceMax?: number;
  bedsMin?: number;
  bathsMin?: number;
}

export interface AutocompleteResponse {
  results: LocationSummary[];
}

export interface DashboardReport {
  id: string;
  location: LocationSummary;
  created_at: string;
  median_price?: string;
}

export interface SavedLocationResponse {
  id: string;
  location: LocationSummary;
  created_at: string;
}

export interface WatchlistEntryResponse {
  id: string;
  location: LocationSummary;
  /** Last 12 median price data points for sparkline */
  price_history: number[];
  created_at: string;
}

export interface InvestmentAnalyticsEntry {
  location: LocationSummary;
  roi_estimate?: string;
  rental_yield?: string;
  median_price?: string;
}
