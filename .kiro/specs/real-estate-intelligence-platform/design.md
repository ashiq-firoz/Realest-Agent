# Design: Real Estate Intelligence Platform

## Overview

This document covers the full technical design for upgrading the Cotality Intelligence MVP into a production-grade real estate intelligence platform for the Australian property market. The upgrade replaces the SQLite/Prisma single-service architecture with a multi-service Docker Compose stack: Next.js 14 (App Router) as the frontend, FastAPI (Python) as the backend data/AI service, PostgreSQL 15 as the primary database, and Redis 7 as the aggregated-data cache.

The existing MVP codebase (`e:/realestate/platform`) continues to run as the starting point. All new backend logic is written in Python/FastAPI. The Next.js app is refactored to remove Prisma/direct-DB calls and route all data operations through the FastAPI service via authenticated HTTP calls.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose Network                    │
│                                                                  │
│  ┌──────────────────┐   HTTP/REST    ┌──────────────────────┐   │
│  │   Next.js 14     │ ─────────────► │   FastAPI (Python)   │   │
│  │  (App Router)    │ ◄───────────── │   Port 8000          │   │
│  │  Port 3000       │   JSON + JWT   │                      │   │
│  │                  │               │  ┌────────────────┐   │   │
│  │  ┌────────────┐  │               │  │  Routers       │   │   │
│  │  │ NextAuth   │  │               │  │  - /auth       │   │   │
│  │  │ (JWT/OAuth)│  │               │  │  - /locations  │   │   │
│  │  └────────────┘  │               │  │  - /reports    │   │   │
│  │                  │               │  │  - /dashboard  │   │   │
│  │  ┌────────────┐  │               │  │  - /watchlist  │   │   │
│  │  │ Tailwind + │  │               │  └────────────────┘   │   │
│  │  │ shadcn/ui  │  │               │                      │   │
│  │  └────────────┘  │               │  ┌────────────────┐   │   │
│  └──────────────────┘               │  │  Services      │   │   │
│                                     │  │  - GeoService  │   │   │
│                                     │  │  - ReportSvc   │   │   │
│                                     │  │  - GeminiSvc   │   │   │
│                                     │  │  - PDFService  │   │   │
│                                     │  │  - CacheService│   │   │
│                                     │  └────────────────┘   │   │
│                                     └──────────┬───────────┘   │
│                                                │                │
│              ┌─────────────────────────────────┤                │
│              │                                 │                │
│  ┌───────────▼──────┐            ┌─────────────▼──────┐        │
│  │  PostgreSQL 15   │            │     Redis 7         │        │
│  │  Port 5432       │            │     Port 6379       │        │
│  │  (SQLAlchemy ORM)│            │  (Aggregated cache) │        │
│  └──────────────────┘            └────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘

External APIs (called by FastAPI only):
  - Nominatim/OpenStreetMap  (geocoding)
  - Domain API               (AU property listings)
  - ABS API                  (demographics)
  - data.gov.au              (government datasets)
  - Google Gemini 1.5 Pro    (AI report generation)
```

### Architectural Principles

**Backend owns all data and AI logic.** Next.js serves only as a presentation layer. No database queries or API calls to external services are made from Next.js routes. This separates concerns, simplifies secret management, and makes the backend independently testable.

**Pre-aggregated data model.** External Australian API data is fetched and stored in PostgreSQL in the background. On user request, the FastAPI service reads from Redis (TTL: 6 hours) or PostgreSQL — never calling Domain/ABS/data.gov.au in the hot path. This eliminates user-facing latency from third-party API round-trips.

**JWT passed through.** NextAuth.js issues a JWT (signed with `NEXTAUTH_SECRET`) after OAuth/credential sign-in. Every request from Next.js to FastAPI includes `Authorization: Bearer <token>`. FastAPI validates the same secret to identify the user without a separate auth database lookup.

**Fallback at every layer.** If Domain API data is absent → use mock data. If ABS data is stale → serve stale with a `data_freshness` flag. If Gemini times out → return partial report with placeholder AI Summary. The platform never returns an empty report.

---

## Technology Stack

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Frontend | Next.js (App Router) | 14.2.x | Existing; refactor API calls |
| UI | Tailwind CSS + shadcn/ui | 3.4.x / latest | Existing; add new components |
| Charts | Recharts | 3.x | Existing; add sparklines |
| Maps | Leaflet + react-leaflet | 1.9.x / 5.x | Existing |
| Auth (frontend) | NextAuth.js | 5.x (beta) | New addition |
| Backend | FastAPI | 0.111.x | New service |
| ORM | SQLAlchemy | 2.x + asyncpg | New |
| Migrations | Alembic | 1.13.x | New |
| AI | google-generativeai | 0.5.x | Port from Next.js |
| PDF | WeasyPrint | 62.x | New |
| Database | PostgreSQL | 15 | Replaces SQLite |
| Cache | Redis | 7 | New |
| Python HTTP client | httpx | 0.27.x | Async external API calls |
| Containers | Docker Compose | 2.x | New |
| Python validation | Pydantic | 2.x | Request/response schemas |

---

## Directory Structure

### New directory: `e:/realestate/realestate-platform-v2/`

```
realestate-platform-v2/
├── docker-compose.yml
├── .env                          # Root env file (all secrets)
├── .env.example
│
├── frontend/                     # Copied/migrated from platform/
│   ├── package.json
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   └── src/
│       ├── app/
│       │   ├── (auth)/
│       │   │   ├── login/page.tsx
│       │   │   └── register/page.tsx
│       │   ├── (app)/
│       │   │   ├── layout.tsx          # Auth-gated layout
│       │   │   ├── dashboard/page.tsx  # Regular + Pro dashboard
│       │   │   ├── report/
│       │   │   │   ├── new/page.tsx
│       │   │   │   └── [id]/page.tsx
│       │   │   └── pro/
│       │   │       ├── watchlist/page.tsx
│       │   │       └── analytics/page.tsx
│       │   ├── share/[token]/page.tsx  # Public shareable report
│       │   ├── layout.tsx
│       │   └── page.tsx
│       ├── components/
│       │   ├── ui/                     # shadcn/ui components
│       │   ├── location-search.tsx     # Nominatim autocomplete
│       │   ├── report-sections/
│       │   │   ├── market-overview.tsx
│       │   │   ├── neighbourhood-insights.tsx
│       │   │   ├── demographics.tsx
│       │   │   ├── investment-intelligence.tsx
│       │   │   ├── comparable-properties.tsx
│       │   │   └── ai-summary.tsx
│       │   ├── dashboard/
│       │   │   ├── report-card.tsx
│       │   │   ├── saved-locations.tsx
│       │   │   ├── watchlist-panel.tsx
│       │   │   └── investment-analytics.tsx
│       │   └── pro-upgrade-prompt.tsx
│       ├── lib/
│       │   ├── api-client.ts           # Typed fetch wrapper for FastAPI
│       │   ├── auth.ts                 # NextAuth config
│       │   └── utils.ts
│       └── types/
│           └── api.ts                  # Shared TypeScript types
│
└── backend/
    ├── requirements.txt
    ├── alembic.ini
    ├── alembic/
    │   └── versions/
    ├── app/
    │   ├── main.py                     # FastAPI app init
    │   ├── config.py                   # Pydantic Settings
    │   ├── database.py                 # Async SQLAlchemy engine
    │   ├── deps.py                     # Dependency injection (DB, auth)
    │   ├── models/                     # SQLAlchemy ORM models
    │   │   ├── user.py
    │   │   ├── location.py
    │   │   ├── report.py
    │   │   ├── saved_location.py
    │   │   ├── watchlist.py
    │   │   └── aggregated_data.py
    │   ├── schemas/                    # Pydantic request/response schemas
    │   │   ├── auth.py
    │   │   ├── location.py
    │   │   ├── report.py
    │   │   └── dashboard.py
    │   ├── routers/
    │   │   ├── auth.py
    │   │   ├── locations.py
    │   │   ├── reports.py
    │   │   ├── dashboard.py
    │   │   └── watchlist.py
    │   ├── services/
    │   │   ├── geo_service.py          # Nominatim integration
    │   │   ├── domain_service.py       # Domain API client
    │   │   ├── abs_service.py          # ABS API client
    │   │   ├── govdata_service.py      # data.gov.au client
    │   │   ├── aggregation_service.py  # Orchestrates all data sources
    │   │   ├── gemini_service.py       # Gemini prompt + response parsing
    │   │   ├── report_service.py       # Report orchestration
    │   │   ├── cache_service.py        # Redis wrapper
    │   │   └── pdf_service.py          # WeasyPrint PDF generation
    │   └── utils/
    │       ├── token.py                # Short token generation
    │       └── validators.py           # Input validation helpers
    └── tests/
        ├── test_geo_service.py
        ├── test_gemini_service.py
        ├── test_report_service.py
        ├── test_validators.py
        └── test_cache_service.py
```

---

## Data Models

### PostgreSQL Schema (SQLAlchemy ORM)

```python
# app/models/user.py
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # None for OAuth
    name: Mapped[Optional[str]] = mapped_column(String(255))
    image: Mapped[Optional[str]] = mapped_column(String(512))
    provider: Mapped[str] = mapped_column(String(50), default="credentials")  # "google" | "credentials"
    tier: Mapped[str] = mapped_column(String(20), default="regular")  # "regular" | "pro"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    reports: Mapped[List["Report"]] = relationship(back_populates="user")
    saved_locations: Mapped[List["SavedLocation"]] = relationship(back_populates="user")
    watchlist_entries: Mapped[List["WatchlistEntry"]] = relationship(back_populates="user")


# app/models/location.py
class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    display_name: Mapped[str] = mapped_column(String(512), nullable=False)
    suburb: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postcode: Mapped[Optional[str]] = mapped_column(String(10))
    country: Mapped[str] = mapped_column(String(100), default="Australia")
    country_code: Mapped[str] = mapped_column(String(3), default="AU")
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    nominatim_place_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    reports: Mapped[List["Report"]] = relationship(back_populates="location")
    aggregated_data: Mapped[List["AggregatedMarketData"]] = relationship(back_populates="location")


# app/models/report.py
class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), nullable=False)
    share_token: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    # 6 report sections stored as TEXT (Markdown / JSON)
    market_overview: Mapped[Optional[str]] = mapped_column(Text)
    neighbourhood_insights: Mapped[Optional[str]] = mapped_column(Text)
    demographics_section: Mapped[Optional[str]] = mapped_column(Text)
    investment_intelligence: Mapped[Optional[str]] = mapped_column(Text)
    comparable_properties: Mapped[Optional[str]] = mapped_column(Text)   # JSON array
    ai_summary: Mapped[Optional[str]] = mapped_column(Text)
    # Aggregated market metrics for dashboard cards
    median_price: Mapped[Optional[str]] = mapped_column(String(50))
    price_appreciation: Mapped[Optional[str]] = mapped_column(String(50))
    rental_yield: Mapped[Optional[str]] = mapped_column(String(50))
    days_on_market: Mapped[Optional[int]] = mapped_column(Integer)
    roi_estimate: Mapped[Optional[str]] = mapped_column(String(50))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)  # soft-delete
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped["User"] = relationship(back_populates="reports")
    location: Mapped["Location"] = relationship(back_populates="reports")


# app/models/saved_location.py
class SavedLocation(Base):
    __tablename__ = "saved_locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped["User"] = relationship(back_populates="saved_locations")
    location: Mapped["Location"] = relationship()


# app/models/watchlist.py
class WatchlistEntry(Base):
    __tablename__ = "watchlist_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped["User"] = relationship(back_populates="watchlist_entries")
    location: Mapped["Location"] = relationship()


# app/models/aggregated_data.py
class AggregatedMarketData(Base):
    __tablename__ = "aggregated_market_data"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), nullable=False)
    data_source: Mapped[str] = mapped_column(String(50))   # "domain" | "abs" | "govdata" | "mock"
    data_type: Mapped[str] = mapped_column(String(50))     # "listings" | "demographics" | "market"
    payload: Mapped[str] = mapped_column(Text)             # JSON blob
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    location: Mapped["Location"] = relationship(back_populates="aggregated_data")
```

### Canonical Data Schemas (Pydantic)

```python
# app/schemas/report.py

class PropertyListing(BaseModel):
    """Canonical schema after Domain API normalization."""
    address: str
    price: str                      # Formatted: "$450,000"
    price_numeric: Optional[int]    # For sorting/filtering
    beds: int
    baths: float
    sqft: Optional[int]
    listing_type: Literal["sold", "active", "leased"]
    property_type: Literal["house", "unit", "townhouse", "land", "other"]
    listed_at: Optional[date]
    source: str = "domain"


class DemographicsSnapshot(BaseModel):
    """Canonical schema after ABS API normalization."""
    population: int
    population_growth_pct: float    # Annual %
    median_age: int
    median_household_income: int    # AUD
    unemployment_rate: float        # %
    dominant_age_group: str
    reference_year: int
    source: str = "abs"


class MarketMetrics(BaseModel):
    """Aggregated market statistics."""
    median_sale_price: int
    median_rent_weekly: int
    price_appreciation_yoy: float   # %
    rental_yield: float             # %
    days_on_market: int
    clearance_rate: Optional[float]
    inventory_level: Literal["low", "medium", "high"]
    market_sentiment: Literal["buyers", "balanced", "sellers"]


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
    comparable_properties: List[PropertyListing]
    ai_summary: str
    median_price: Optional[str]
    price_appreciation: Optional[str]
    rental_yield: Optional[str]
    days_on_market: Optional[int]
    roi_estimate: Optional[str]
    created_at: datetime
```

---

## API Design (FastAPI Routers)

### Authentication Routes (`/auth`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | None | Register with email + password |
| POST | `/auth/login` | None | Login, returns JWT |
| POST | `/auth/google` | None | Exchange Google OAuth token for app JWT |
| GET | `/auth/me` | JWT | Get current user profile |

### Location Routes (`/locations`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/locations/autocomplete?q={query}` | None | Nominatim autocomplete (AU only) |
| GET | `/locations/{id}` | JWT | Get location details |

### Report Routes (`/reports`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/reports` | JWT | Generate new report for location |
| GET | `/reports/{id}` | JWT (owner) | Get full report |
| DELETE | `/reports/{id}` | JWT (owner) | Soft-delete report |
| GET | `/reports/share/{token}` | None | Public shareable report |
| GET | `/reports/{id}/export/pdf` | JWT | Stream PDF export |

### Dashboard Routes (`/dashboard`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/dashboard/reports` | JWT | Paginated user report list (max 20) |
| POST | `/dashboard/saved-locations` | JWT (Pro) | Save a location |
| GET | `/dashboard/saved-locations` | JWT (Pro) | List saved locations |
| DELETE | `/dashboard/saved-locations/{id}` | JWT (Pro) | Remove saved location |
| GET | `/dashboard/analytics` | JWT (Pro) | Investment analytics aggregation |

### Watchlist Routes (`/watchlist`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/watchlist` | JWT (Pro) | Add location to watchlist |
| GET | `/watchlist` | JWT (Pro) | List watchlist with sparkline data |
| DELETE | `/watchlist/{id}` | JWT (Pro) | Remove watchlist entry |

---

## Components and Interfaces

### Frontend Components

#### `LocationSearch` (`components/location-search.tsx`)

Renders the main search input with Nominatim autocomplete. Debounces input (300ms) before calling the FastAPI `/locations/autocomplete` endpoint. Displays a dropdown of up to 8 results with suburb, city, and state. On selection, stores the full location object in component state and calls `onLocationSelect(location)` callback.

```typescript
interface LocationSearchProps {
  onLocationSelect: (location: LocationSummary) => void;
  placeholder?: string;
  autoFocus?: boolean;
}
```

#### `ReportSections` (`components/report-sections/`)

Each section is a separate, independently importable React component that accepts typed props and renders its section content. This allows lazy loading and individual skeleton states.

```typescript
// comparable-properties.tsx
interface ComparablePropertiesProps {
  properties: PropertyListing[];
  isPro: boolean;
  onFilterChange?: (filters: PropertyFilters) => void;  // Pro only
}

interface PropertyFilters {
  propertyType?: "house" | "unit" | "townhouse" | "land" | "other";
  priceMin?: number;
  priceMax?: number;
  bedsMin?: number;
  bathsMin?: number;
}
```

#### `ProUpgradePrompt` (`components/pro-upgrade-prompt.tsx`)

Modal/inline component shown when a Regular user attempts to access a Pro feature. Accepts a `featureName` prop to customize the copy.

#### `WatchlistPanel` (`components/dashboard/watchlist-panel.tsx`)

Renders saved watchlist locations with a Recharts `<Sparkline>` showing median price trend over the last 12 data points. Data fetched from `/watchlist`.

### Frontend API Client (`lib/api-client.ts`)

Typed wrapper around `fetch` that automatically attaches the NextAuth session JWT, handles 401 redirects, and provides response type inference.

```typescript
export async function apiGet<T>(path: string, session: Session): Promise<T>
export async function apiPost<T, B>(path: string, body: B, session: Session): Promise<T>
export async function apiDelete(path: string, session: Session): Promise<void>
```

---

## Service Design (FastAPI Backend)

### `GeoService` (`services/geo_service.py`)

Handles all Nominatim interactions. Adds `countrycodes=au` to all queries to restrict to Australian results. Parses the Nominatim JSON response into the `LocationSummary` Pydantic schema. Returns at most 8 results sorted by `importance` descending.

```python
class GeoService:
    BASE_URL = "https://nominatim.openstreetmap.org/search"

    async def autocomplete(self, query: str) -> list[LocationSummary]:
        """Query Nominatim with AU restriction. Returns ≤8 results."""
        ...

    def parse_nominatim_result(self, result: dict) -> LocationSummary:
        """Extract suburb, city, state, postcode, lat/lon from Nominatim address object."""
        ...

    def is_australian(self, location: LocationSummary) -> bool:
        """Return True iff country_code == 'AU'."""
        return location.country_code.upper() == "AU"
```

### `AggregationService` (`services/aggregation_service.py`)

Orchestrates parallel fetching from Domain API, ABS API, and data.gov.au. Uses `asyncio.gather` with individual `try/except` per source so a single API failure does not abort the pipeline. Writes results to PostgreSQL `aggregated_market_data` table with `is_stale=True` on failure.

```python
class AggregationService:
    async def aggregate_for_location(
        self, location_id: str, db: AsyncSession
    ) -> AggregatedDataBundle:
        """
        Runs all data sources in parallel.
        Falls back to mock data if a source fails.
        Returns AggregatedDataBundle with populated fields and data_freshness flags.
        """
        results = await asyncio.gather(
            self._fetch_domain(location_id),
            self._fetch_abs(location_id),
            self._fetch_govdata(location_id),
            return_exceptions=True,
        )
        return self._merge_with_fallbacks(results)

    def _merge_with_fallbacks(
        self, results: tuple
    ) -> AggregatedDataBundle:
        """
        For each result: if it's an exception, substitute mock data
        and mark that source as stale.
        """
        ...
```

### `GeminiService` (`services/gemini_service.py`)

Constructs the structured prompt, calls the Gemini 1.5 Pro API, and parses the 6-section response. Implements a single retry with correction instruction if any sections are missing from the initial response.

```python
REQUIRED_SECTIONS = [
    "Market Overview",
    "Neighbourhood Insights",
    "Demographics",
    "Investment Intelligence",
    "Comparable Properties",
    "AI Summary",
]

class GeminiService:
    def build_prompt(self, location: LocationSummary, data: AggregatedDataBundle) -> str:
        """
        Returns a prompt string containing:
        - Location context
        - JSON data block with market metrics, demographics, and listings
        - Explicit instruction to produce all 6 sections in Markdown
        """
        ...

    def parse_sections(self, response_text: str) -> dict[str, str]:
        """
        Extracts each of the 6 sections from the Markdown response.
        Uses regex anchored to known section headers.
        Returns dict with section name → content.
        """
        ...

    def validate_sections(self, sections: dict[str, str]) -> list[str]:
        """Returns list of missing section names. Empty list = all present."""
        return [s for s in REQUIRED_SECTIONS if s not in sections or not sections[s].strip()]

    async def generate_report(
        self, location: LocationSummary, data: AggregatedDataBundle
    ) -> dict[str, str]:
        """
        Calls Gemini. If validate_sections finds missing sections,
        re-prompts once with correction instruction. Returns final sections dict.
        On Gemini error, returns sections dict with AI Summary placeholder.
        """
        ...
```

### `CacheService` (`services/cache_service.py`)

Wraps Redis with typed get/set operations. Uses JSON serialization. Cache keys follow the pattern `aggregated:{location_id}`. TTL is read from `settings.CACHE_TTL_SECONDS` (default: 21600 = 6 hours).

```python
class CacheService:
    async def get_aggregated(self, location_id: str) -> AggregatedDataBundle | None: ...
    async def set_aggregated(self, location_id: str, data: AggregatedDataBundle) -> None: ...
    async def invalidate(self, location_id: str) -> None: ...
```

### `PDFService` (`services/pdf_service.py`)

Renders report data into an HTML template using Python string formatting, then uses WeasyPrint to convert to PDF bytes. The HTML template is stored in `backend/templates/report.html` and includes Cotality Intelligence branding, all 6 sections, and a generation date footer.

```python
class PDFService:
    async def generate(self, report: ReportResponse) -> bytes:
        """Returns PDF bytes for the given report."""
        html = self._render_html(report)
        return HTML(string=html).write_pdf()

    def _render_html(self, report: ReportResponse) -> str:
        """Renders the Jinja2 HTML template with report data."""
        ...
```

### `ReportService` (`services/report_service.py`)

Orchestrates the full report generation pipeline:

1. Look up the location by `location_id`
2. Check Redis cache for aggregated data
3. If cache miss: run `AggregationService.aggregate_for_location()`, cache result
4. Run `GeminiService.generate_report()`
5. Generate a unique 8-character URL-safe share token via `token.generate_share_token()`
6. Persist all sections to the `reports` table
7. Return the full `ReportResponse`

---

## Authentication Design

### NextAuth.js Configuration (`frontend/src/lib/auth.ts`)

```typescript
export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    CredentialsProvider({
      credentials: {
        email: { type: "email" },
        password: { type: "password" },
      },
      async authorize(credentials) {
        // POST to FastAPI /auth/login
        const res = await fetch(`${process.env.BACKEND_URL}/auth/login`, {
          method: "POST",
          body: JSON.stringify(credentials),
        });
        if (!res.ok) return null;
        return res.json();  // { id, email, name, tier, token }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.backendToken = user.token;
        token.tier = user.tier;
      }
      return token;
    },
    async session({ session, token }) {
      session.backendToken = token.backendToken;
      session.user.tier = token.tier;
      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET,
};
```

### FastAPI JWT Dependency (`deps.py`)

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validates the Bearer JWT using NEXTAUTH_SECRET.
    Raises 401 if token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.NEXTAUTH_SECRET,
            algorithms=["HS256"],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get(User, user_id)
    if not user:
        raise credentials_exception
    return user


async def require_pro(user: User = Depends(get_current_user)) -> User:
    """Raises 403 if user is not Pro tier."""
    if user.tier != "pro":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    return user
```

---

## Caching Strategy

```
User Request
     │
     ▼
FastAPI /reports [POST]
     │
     ▼
CacheService.get_aggregated(location_id)
     │
     ├─── HIT ──► Return cached AggregatedDataBundle
     │              (skip Domain/ABS/GovData calls)
     │
     └─── MISS ──► AggregationService.aggregate_for_location()
                        │
                        ├── Domain API    (async, with fallback)
                        ├── ABS API       (async, with fallback)
                        └── GovData API   (async, with fallback)
                        │
                        ▼
                   Merge + CacheService.set_aggregated()
                   (TTL = CACHE_TTL_SECONDS, default 6h)
                        │
                        ▼
                   GeminiService.generate_report()
                        │
                        ▼
                   Persist Report to PostgreSQL
                        │
                        ▼
                   Return ReportResponse
```

Redis key schema:
- `aggregated:{location_id}` — AggregatedDataBundle JSON, TTL 6h
- `report:{report_id}` — Full ReportResponse JSON, TTL 24h (read-through cache for report pages)

---

## Docker Compose Configuration

```yaml
# docker-compose.yml (conceptual — full file in implementation)
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      NEXTAUTH_SECRET: ${NEXTAUTH_SECRET}
      DOMAIN_API_KEY: ${DOMAIN_API_KEY}
      CACHE_TTL_SECONDS: ${CACHE_TTL_SECONDS:-21600}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    command: >
      sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"

  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000
      BACKEND_URL: http://backend:8000
      NEXTAUTH_SECRET: ${NEXTAUTH_SECRET}
      NEXTAUTH_URL: http://localhost:3000
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
    depends_on:
      - backend
    ports:
      - "3000:3000"

volumes:
  postgres_data:
  redis_data:
```

---

## Error Handling

### FastAPI Error Hierarchy

```python
# All service exceptions map to HTTP status codes via exception handlers

class AppException(Exception):
    def __init__(self, message: str, status_code: int = 500): ...

class LocationNotFoundError(AppException):   # 404
class GeocodeError(AppException):            # 503 (external dependency)
class ReportGenerationError(AppException):   # 500
class GeminiError(AppException):             # 503 (with partial report fallback)
class CacheError(AppException):              # 503 (non-fatal, log and continue)
class PDFGenerationError(AppException):      # 500
class TierError(AppException):               # 403
```

### Fallback Chain for Report Generation

1. **Domain API fails** → Use mock Australian property listings
2. **ABS API fails** → Use last cached demographics from PostgreSQL; if absent, use ABS mock data
3. **data.gov.au fails** → Mark section as unavailable; Gemini prompt omits that context
4. **Gemini API fails / times out** → Return partial report with AI Summary = placeholder message; log error; do not fail the entire request
5. **PDF generation fails** → Return 500 with error detail; do not affect report viewing

### Frontend Error Handling

All API calls in Next.js route through `api-client.ts`, which handles:
- `401` → `signOut()` and redirect to `/login?callbackUrl={current}`
- `403` → Show `ProUpgradePrompt` modal
- `503` → Show toast "Service temporarily unavailable, please try again"
- `5xx` → Show error toast with retry button

---

## Key Flows

### Report Generation Flow (Sequence)

```
Browser          Next.js          FastAPI           Redis       PostgreSQL    Gemini
  │                │                  │               │              │           │
  │ POST /report   │                  │               │              │           │
  │ new?location=..│                  │               │              │           │
  │────────────────►                  │               │              │           │
  │                │ POST /reports    │               │              │           │
  │                │ {location_id}    │               │              │           │
  │                │──────────────────►               │              │           │
  │                │                  │ GET aggregated│              │           │
  │                │                  │───────────────►              │           │
  │                │                  │    MISS        │              │           │
  │                │                  │◄───────────────              │           │
  │                │                  │ parallel fetch (Domain+ABS+GovData)      │
  │                │                  │──────────────────────────────────────────┤
  │                │                  │◄─────────────────────────────────────────┤
  │                │                  │ SET aggregated│              │           │
  │                │                  │───────────────►              │           │
  │                │                  │ generate prompt + call Gemini│           │
  │                │                  │──────────────────────────────────────────►
  │                │                  │◄─────────────────────────────────────────
  │                │                  │ INSERT report │              │           │
  │                │                  │──────────────────────────────►           │
  │                │                  │◄──────────────────────────────           │
  │                │    {report_id}   │               │              │           │
  │                │◄─────────────────               │              │           │
  │ redirect       │                  │               │              │           │
  │ /report/{id}   │                  │               │              │           │
  ◄────────────────┤                  │               │              │           │
```

### Shareable Link Flow

1. Report is created → `share_token` (8-char URL-safe) stored in `reports.share_token`
2. User clicks "Share" → frontend constructs `{NEXTAUTH_URL}/share/{share_token}` → copied to clipboard
3. Recipient opens `/share/{token}` → Next.js page calls FastAPI `GET /reports/share/{token}` (no auth required)
4. FastAPI returns full `ReportResponse`; page renders all 6 sections in read-only mode

---

## Migration from Existing MVP

The existing `e:/realestate/platform` MVP uses:
- SQLite via Prisma (replaced by PostgreSQL via SQLAlchemy/Alembic)
- Direct Gemini calls from Next.js API routes (moved to FastAPI `GeminiService`)
- Hardcoded mock data in `generate-report/route.ts` (moved to `AggregationService` with real API integration + mock fallback)
- No auth (replaced by NextAuth.js + JWT)
- No caching (replaced by Redis `CacheService`)

Migration steps are documented in the tasks list. The existing report data structure is compatible with the new schema — the 4 JSON fields (`marketSummary`, `investmentIndicators`, `demographics`, `comparableProperties`) map directly to the new 6-section model with `market_overview` and `neighbourhood_insights` split from the old `marketSummary`.

---

## Testing Strategy

### Dual Testing Approach

The platform uses both example-based unit tests and property-based tests. Unit tests verify specific scenarios, integration points, and edge conditions. Property tests verify universal behaviors across a wide range of generated inputs.

**Unit Tests** (example-based) focus on:
- Specific OAuth and credential login flows (auth examples with concrete inputs)
- Empty dashboard empty-state rendering
- Report card navigation behavior
- PDF export error handling
- Pro upgrade prompt rendering for Regular users
- Smoke tests for Docker Compose service startup and Alembic migrations

**Property Tests** (property-based) focus on:
- `GeoService.parse_nominatim_result` — result completeness across varied Nominatim response shapes
- `GeoService.is_australian` — country code filtering over random location objects
- `AggregationService._merge_with_fallbacks` — bundle completeness under all 2³ API availability combinations
- `GeminiService.parse_sections` / `validate_sections` — parsing and validation over randomly structured response strings
- `token.generate_share_token` — uniqueness and format over large generated batches
- `CacheService` get/set — idempotence with mocked Redis
- `PDFService.generate` — content completeness over random report fixtures
- Dashboard query ordering / limit — over randomly sized and ordered report collections
- `ComparableProperties` filter — correctness over random property arrays and filter combinations
- Domain and ABS normalizers — schema completeness over randomly shaped API response objects
- Pydantic Settings validation — startup failure over subsets of env var configurations

**Property Test Configuration:**
- Minimum 100 iterations per property test (Hypothesis for Python backend, fast-check for TypeScript frontend)
- Tag format for backend: `@settings(max_examples=100)` + `@given(...)` Hypothesis decorators
- Each property test references its design document property via a docstring annotation: `# Property N: {title}`

### Test File Mapping

| Test File | Test Type | Properties Covered |
|-----------|-----------|-------------------|
| `tests/test_geo_service.py` | Property | P1, P2 |
| `tests/test_validators.py` | Property | P3, P4, P5 |
| `tests/test_aggregation_service.py` | Property | P6 |
| `tests/test_gemini_service.py` | Property | P7, P10, P24 |
| `tests/test_token.py` | Property | P8 |
| `tests/test_cache_service.py` | Property | P9 |
| `tests/test_report_service.py` | Integration | P10, P11 |
| `tests/test_pdf_service.py` | Property | P15 |
| `tests/test_dashboard_queries.py` | Property | P16, P17, P18, P19 |
| `tests/test_auth_deps.py` | Property | P20 |
| `tests/test_normalizers.py` | Property | P22 |
| `tests/test_config.py` | Property | P23 |

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

---

### Property 1: Autocomplete Results Are Bounded and Australian

*For any* query string of 2 or more characters, the autocomplete function shall return at most 8 results, and every result in the returned list shall have `country_code == "AU"`.

**Validates: Requirements 1.1, 1.4**

---

### Property 2: Location Resolution Completeness

*For any* valid Nominatim API response object, the `parse_nominatim_result` function shall return a `LocationSummary` where all required fields (`display_name`, `city`, `state`, `country_code`, `latitude`, `longitude`) are non-null and non-empty strings (or valid floats for coordinates).

**Validates: Requirements 1.2**

---

### Property 3: Password Validation Rejects Invalid Inputs

*For any* registration input where the email field is syntactically invalid (no `@`, no domain) or the password field has fewer than 8 characters, the validator shall return a non-empty validation error and shall not create a user record.

**Validates: Requirements 2.3**

---

### Property 4: Bcrypt Cost Invariant

*For any* plaintext password string submitted to the registration endpoint, the stored `hashed_password` shall be a valid bcrypt hash with a cost factor of 12 or greater, as verifiable by decoding the hash prefix.

**Validates: Requirements 2.2**

---

### Property 5: JWT Identity Round-Trip

*For any* valid JWT token issued by the auth service, decoding it with the `NEXTAUTH_SECRET` shall produce a payload where `sub` equals the `user.id` that was used to issue the token, and the `exp` claim shall be approximately 24 hours after the `iat` claim (within 60-second tolerance).

**Validates: Requirements 2.1, 2.4, 2.5**

---

### Property 6: Data Aggregation Completeness Under Partial Failure

*For any* combination of available and unavailable external data sources (Domain API, ABS API, data.gov.au), the `AggregationService.aggregate_for_location` function shall return an `AggregatedDataBundle` where all required top-level fields (`listings`, `demographics`, `market_metrics`) are populated (with mock/stale data where the source was unavailable), and sources that failed shall have `is_stale=True`.

**Validates: Requirements 3.1, 9.2**

---

### Property 7: Gemini Response Section Parsing

*For any* Gemini response string that contains all 6 required section headers, `GeminiService.parse_sections` shall return a dictionary with exactly 6 keys, each mapping to a non-empty string. *For any* response string with one or more missing sections, `validate_sections` shall return a non-empty list of the missing section names.

**Validates: Requirements 3.3, 11.2**

---

### Property 8: Share Token Uniqueness and Format

*For any* collection of generated share tokens, each token shall be exactly 8 characters in length, consist only of URL-safe characters (alphanumeric, `-`, `_`), and no two tokens in the collection shall be identical.

**Validates: Requirements 3.4**

---

### Property 9: Cache Hit Idempotence

*For any* location that has been cached in Redis, calling `AggregationService.aggregate_for_location` again within the TTL window shall return data equal to the cached bundle without invoking any external API calls (verifiable via mock call counters).

**Validates: Requirements 3.5, 9.3**

---

### Property 10: Partial Report on Gemini Failure

*For any* Gemini API error condition (timeout, rate limit, network error), `GeminiService.generate_report` shall return a sections dictionary where the 5 non-AI sections are populated with data derived from the `AggregatedDataBundle`, and `ai_summary` is set to a non-empty placeholder string (not an empty string or null).

**Validates: Requirements 3.7**

---

### Property 11: Report Rendering Completeness

*For any* `ReportResponse` object with all 6 sections populated, the rendered report page shall contain all 6 section headings and at least one of each key metric (`median_price`, `price_appreciation`, `rental_yield`, `days_on_market`, `roi_estimate`) rendered in the DOM.

**Validates: Requirements 4.1, 4.2**

---

### Property 12: Comparable Properties Table Integrity

*For any* array of `PropertyListing` objects of length N ≥ 0, the rendered comparable properties table shall contain exactly N data rows and exactly the defined column headers (`address`, `price`, `beds`, `baths`, `sqft`, `listing_type`).

**Validates: Requirements 4.3**

---

### Property 13: Share Link Format Invariant

*For any* report with a non-null `share_token`, the generated shareable URL shall match the pattern `{base_url}/share/{share_token}` where `share_token` is the exact token stored on the report.

**Validates: Requirements 4.4**

---

### Property 14: Read-Only Mode for Non-Owners

*For any* `(user_id, report_id)` pair where `user_id != report.user_id`, the rendered report page shall not contain edit or delete controls, regardless of the user's tier.

**Validates: Requirements 4.6**

---

### Property 15: PDF Content Completeness

*For any* `ReportResponse` object, the PDF bytes produced by `PDFService.generate` shall, when parsed as text, contain the location `display_name`, all 6 section headings, the string "Cotality Intelligence", and the report `created_at` date formatted as a string.

**Validates: Requirements 5.2**

---

### Property 16: Dashboard Ordering and Limit

*For any* user with N reports (N ≥ 0), the `/dashboard/reports` endpoint shall return min(N, 20) reports ordered strictly by `created_at` descending (each report's timestamp shall be ≥ the timestamp of the next report in the list).

**Validates: Requirements 6.1**

---

### Property 17: Soft-Delete Visibility

*For any* report that has been soft-deleted (i.e., `is_deleted=True`), subsequent calls to `/dashboard/reports` and `/reports/{id}` for the owning user shall not include that report in the response.

**Validates: Requirements 6.4**

---

### Property 18: Saved Location Round-Trip

*For any* `location_id` saved via `POST /dashboard/saved-locations` for a Pro user, a subsequent `GET /dashboard/saved-locations` for the same user shall include an entry with that `location_id`.

**Validates: Requirements 7.2**

---

### Property 19: Investment Analytics Ordering

*For any* Pro user with a set of saved locations that have `roi_estimate` values, the `/dashboard/analytics` response shall return those locations sorted by `roi_estimate` descending, with each entry containing `location_id`, `roi_estimate`, and `rental_yield`.

**Validates: Requirements 7.4**

---

### Property 20: Pro Feature Gate

*For any* Regular-tier user, requests to Pro-only endpoints (`/dashboard/saved-locations`, `/dashboard/analytics`, `/watchlist`) shall receive an HTTP 403 response, and the corresponding frontend components shall render the `ProUpgradePrompt` instead of feature content.

**Validates: Requirements 7.5, 8.4**

---

### Property 21: Comparable Properties Filter Correctness

*For any* array of `PropertyListing` objects and any `PropertyFilters` object with one or more active predicates, the filtered result shall contain only and exactly those listings that satisfy all active predicates simultaneously (type match, price within range, beds ≥ min, baths ≥ min).

**Validates: Requirements 8.2**

---

### Property 22: Data Normalization Schema Completeness

*For any* valid Domain API property listing response object and any valid ABS demographics response object, their respective normalizer functions shall produce output objects where every required field in `PropertyListing` and `DemographicsSnapshot` respectively is present and of the correct type.

**Validates: Requirements 9.4, 9.5**

---

### Property 23: Environment Variable Startup Validation

*For any* subset of required environment variables that is missing at least one variable, the FastAPI startup validation shall raise a `ValidationError` (Pydantic Settings) and the service shall not start, with the error message containing the name of at least one missing variable.

**Validates: Requirements 10.3**

---

### Property 24: Gemini Prompt Data Completeness

*For any* `AggregatedDataBundle` object with non-null `market_metrics`, `demographics`, and `listings` fields, the prompt string produced by `GeminiService.build_prompt` shall contain a JSON-formatted block that includes the serialized representation of all three data categories and explicitly names all 6 required report sections.

**Validates: Requirements 11.1**
