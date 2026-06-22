# Implementation Plan: Real Estate Intelligence Platform

## Overview

Upgrade the Cotality Intelligence MVP into a production-grade multi-service platform. The implementation migrates from the existing SQLite/Prisma single-service Next.js app (`e:/realestate/platform`) to a Docker Compose stack comprising: FastAPI (Python) backend, PostgreSQL 15, Redis 7, and a refactored Next.js 14 frontend. All 24 correctness properties from the design are covered by property-based tests (Hypothesis/Python, fast-check/TypeScript).

---

## Tasks

- [x] 1. Project scaffolding and infrastructure
  - [x] 1.1 Create Docker Compose and root environment files
    - Create `e:/realestate/realestate-platform-v2/docker-compose.yml` with services: `postgres` (postgres:15-alpine), `redis` (redis:7-alpine), `backend`, `frontend`
    - Add named volumes `postgres_data` and `redis_data` for data persistence
    - Configure `postgres` healthcheck (`pg_isready`) so `backend` depends on it with `condition: service_healthy`
    - Add `backend` command: `sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"`
    - Create `.env` with all required variables: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `REDIS_URL`, `GEMINI_API_KEY`, `NEXTAUTH_SECRET`, `DOMAIN_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `CACHE_TTL_SECONDS`
    - Create `.env.example` with placeholder values for every variable
    - _Requirements: 10.1, 10.2, 10.3, 10.5_

  - [x] 1.2 Scaffold FastAPI backend directory
    - Create `backend/` directory with `requirements.txt` listing: `fastapi==0.111.*`, `uvicorn[standard]`, `sqlalchemy[asyncio]==2.*`, `asyncpg`, `alembic==1.13.*`, `pydantic[email]==2.*`, `pydantic-settings`, `python-jose[cryptography]`, `passlib[bcrypt]`, `httpx==0.27.*`, `redis[asyncio]`, `google-generativeai==0.5.*`, `weasyprint==62.*`, `hypothesis`, `pytest`, `pytest-asyncio`
    - Create `backend/app/__init__.py`, `backend/app/main.py` (FastAPI app init with CORS, exception handlers, router registration), `backend/app/config.py` (Pydantic Settings reading from env)
    - Create `backend/app/database.py` with async SQLAlchemy engine and `AsyncSession` factory
    - Create `backend/Dockerfile` using `python:3.12-slim`, installing WeasyPrint system dependencies (`libpango-1.0`, `libgdk-pixbuf-2.0`), copying `requirements.txt`, running `pip install`, copying `app/`
    - Create `backend/alembic.ini` and `backend/alembic/env.py` wired to the async engine
    - _Requirements: 10.1, 10.2, 10.3_

  - [x] 1.3 Scaffold Next.js frontend directory
    - Copy existing `e:/realestate/platform` source into `frontend/` as the migration base
    - Remove Prisma dependencies from `frontend/package.json`; add `next-auth@5.x`, `react-markdown`, `fast-check`
    - Create `frontend/Dockerfile` using `node:20-alpine`, running `npm ci` and `npm run build`
    - Create `frontend/src/lib/api-client.ts` with typed `apiGet<T>`, `apiPost<T,B>`, `apiDelete` functions that attach the NextAuth session JWT as `Authorization: Bearer`; handle 401 (signOut + redirect), 403 (throw ProError), 503/5xx (throw ServiceError)
    - Create `frontend/src/types/api.ts` with TypeScript interfaces matching all Pydantic response schemas (`LocationSummary`, `ReportResponse`, `PropertyListing`, `DemographicsSnapshot`, `MarketMetrics`, `PropertyFilters`)
    - _Requirements: 10.1_

- [x] 2. Backend data models and database migrations
  - [x] 2.1 Implement SQLAlchemy ORM models
    - Create `backend/app/models/user.py` — `User` model with fields: `id` (UUID), `email`, `hashed_password` (nullable), `name`, `image`, `provider`, `tier`, `created_at`, `updated_at`; relationships to `reports`, `saved_locations`, `watchlist_entries`
    - Create `backend/app/models/location.py` — `Location` model with fields: `id`, `display_name`, `suburb`, `city`, `state`, `postcode`, `country`, `country_code`, `latitude`, `longitude`, `nominatim_place_id`, `created_at`; relationships to `reports`, `aggregated_data`
    - Create `backend/app/models/report.py` — `Report` model with fields: `id`, `user_id` (FK), `location_id` (FK), `share_token` (unique, 8 chars), `market_overview`, `neighbourhood_insights`, `demographics_section`, `investment_intelligence`, `comparable_properties` (JSON text), `ai_summary`, `median_price`, `price_appreciation`, `rental_yield`, `days_on_market`, `roi_estimate`, `is_deleted`, `created_at`
    - Create `backend/app/models/saved_location.py`, `backend/app/models/watchlist.py`, `backend/app/models/aggregated_data.py` per design spec
    - Create `backend/alembic/versions/001_initial_schema.py` auto-generated migration covering all tables
    - _Requirements: 3.3, 3.4, 6.4, 7.2, 7.3, 9.1_

  - [x] 2.2 Implement Pydantic schemas
    - Create `backend/app/schemas/auth.py` — `RegisterRequest`, `LoginRequest`, `TokenResponse`, `UserResponse`
    - Create `backend/app/schemas/location.py` — `LocationSummary`, `AutocompleteResponse`
    - Create `backend/app/schemas/report.py` — `PropertyListing`, `DemographicsSnapshot`, `MarketMetrics`, `ReportGenerationRequest`, `ReportResponse`, `AggregatedDataBundle`, `PropertyFilters`
    - Create `backend/app/schemas/dashboard.py` — `DashboardReport`, `SavedLocationResponse`, `WatchlistEntryResponse`, `InvestmentAnalyticsEntry`
    - _Requirements: 9.4, 9.5_

  - [x] 2.3 Write property tests for data normalizers (P22)
    - **Property 22: Data Normalization Schema Completeness**
    - **Validates: Requirements 9.4, 9.5**
    - In `backend/tests/test_normalizers.py`, use `@given(st.fixed_dictionaries(...))` to generate random-shaped Domain API listing objects and ABS demographics objects; assert every required field in `PropertyListing` and `DemographicsSnapshot` is present and of correct type after normalization
    - Minimum 100 examples per strategy (`@settings(max_examples=100)`)

- [x] 3. Authentication — FastAPI backend
  - [x] 3.1 Implement auth utilities and dependencies
    - Create `backend/app/utils/token.py` — `generate_share_token()` returning exactly 8 URL-safe characters (alphanumeric, `-`, `_`) using `secrets.token_urlsafe`; `create_jwt(user_id, tier)` returning HS256 JWT with `exp = iat + 86400s`
    - Create `backend/app/deps.py` — `get_db()` async session factory dependency; `get_current_user()` dependency that decodes Bearer JWT with `NEXTAUTH_SECRET`, loads `User` from DB, raises 401 on failure; `require_pro()` dependency that raises 403 if `user.tier != "pro"`
    - _Requirements: 2.1, 2.4, 3.4_

  - [x] 3.2 Write property tests for share token and JWT (P5, P8)
    - **Property 5: JWT Identity Round-Trip**
    - **Property 8: Share Token Uniqueness and Format**
    - **Validates: Requirements 2.1, 2.4, 2.5, 3.4**
    - In `backend/tests/test_token.py`, use `@given(st.uuids())` to verify `create_jwt` round-trip: decoded `sub` equals input `user_id`, `exp - iat` is within `[86340, 86460]` seconds
    - Generate batches of 1 000 tokens; assert all are 8 chars, all URL-safe, and `len(set(batch)) == 1000`

  - [x] 3.3 Implement auth router
    - Create `backend/app/routers/auth.py` with endpoints: `POST /auth/register` (hash password with bcrypt cost 12, insert User, return JWT), `POST /auth/login` (verify bcrypt hash, return JWT), `POST /auth/google` (accept Google OAuth token, upsert User with `provider="google"`, return JWT), `GET /auth/me` (return current user via `get_current_user`)
    - Input validation via Pydantic: reject email without `@` + domain, reject password shorter than 8 chars — return 422 with field-level error messages
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.4 Write property tests for password validation and bcrypt invariant (P3, P4)
    - **Property 3: Password Validation Rejects Invalid Inputs**
    - **Property 4: Bcrypt Cost Invariant**
    - **Validates: Requirements 2.2, 2.3**
    - In `backend/tests/test_validators.py`, use `@given(st.emails() | st.text(), st.text(max_size=7))` to assert validator returns non-empty error and does not persist User for bad inputs
    - Use `@given(st.text(min_size=8, max_size=64))` to register valid passwords; decode the stored hash prefix and assert cost factor `>= 12`

  - [x] 3.5 Write property tests for JWT auth dependency (P5, P20)
    - **Property 5: JWT Identity Round-Trip**
    - **Property 20: Pro Feature Gate**
    - **Validates: Requirements 2.1, 2.4, 2.5, 7.5, 8.4**
    - In `backend/tests/test_auth_deps.py`, use `@given(st.uuids(), st.sampled_from(["regular", "pro"]))` to generate users; assert `get_current_user` returns correct user for valid token; assert `require_pro` raises 403 for `tier="regular"` over any valid user id

- [x] 4. GeoService and location autocomplete
  - [x] 4.1 Implement GeoService
    - Create `backend/app/services/geo_service.py` with `GeoService` class
    - `autocomplete(query: str)` — call Nominatim `https://nominatim.openstreetmap.org/search` with `countrycodes=au&format=jsonv2&addressdetails=1&limit=8&q={query}`; add `User-Agent: CotalityIntelligence/1.0` header; parse results with `parse_nominatim_result`; filter to `is_australian()`; return ≤ 8 results sorted by `importance` descending; raise `GeocodeError` on HTTP failure
    - `parse_nominatim_result(result: dict)` — extract `display_name`, `suburb` (from `address.suburb` or `address.city_district`), `city` (from `address.city` or `address.town` or `address.village`), `state`, `postcode`, `country_code`, `lat`, `lon`; ensure no required field is null
    - `is_australian(location)` — return `location.country_code.upper() == "AU"`
    - Create `backend/app/routers/locations.py` with `GET /locations/autocomplete?q={query}` (no auth required, min 2 chars) and `GET /locations/{id}` (JWT required)
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 4.2 Write property tests for GeoService (P1, P2)
    - **Property 1: Autocomplete Results Are Bounded and Australian**
    - **Property 2: Location Resolution Completeness**
    - **Validates: Requirements 1.1, 1.2, 1.4**
    - In `backend/tests/test_geo_service.py`, use `@given(st.fixed_dictionaries({...}))` to generate random Nominatim response objects with varied address shapes; assert `parse_nominatim_result` always returns a `LocationSummary` with all required fields non-null
    - Generate random location objects with `country_code` drawn from `st.sampled_from(["AU", "US", "GB", "NZ", ...])` and assert `is_australian` returns True iff `country_code.upper() == "AU"`
    - Mock `httpx.AsyncClient.get` to return lists of 0–20 results; assert output length ≤ 8 and all entries have `country_code == "AU"`

- [x] 5. Data aggregation services
  - [x] 5.1 Implement external API service clients
    - Create `backend/app/services/domain_service.py` — `DomainService.fetch_listings(location: LocationSummary)` calls Domain API; normalizes each listing into `PropertyListing`; returns `list[PropertyListing]`; raises `ServiceUnavailableError` on HTTP failure
    - Create `backend/app/services/abs_service.py` — `ABSService.fetch_demographics(location: LocationSummary)` calls ABS API; normalizes response into `DemographicsSnapshot`; raises `ServiceUnavailableError` on failure
    - Create `backend/app/services/govdata_service.py` — `GovDataService.fetch_market_data(location: LocationSummary)` calls data.gov.au; returns `MarketMetrics` or raises `ServiceUnavailableError`
    - Define mock fallback data constants in each service module for use when the API is unavailable
    - _Requirements: 3.1, 9.1, 9.2, 9.4, 9.5_

  - [x] 5.2 Implement AggregationService with parallel fetch and fallbacks
    - Create `backend/app/services/aggregation_service.py`
    - `aggregate_for_location(location_id, db)` — check `CacheService`; on miss: run `asyncio.gather(domain, abs, govdata, return_exceptions=True)`; for each result: if Exception → use mock data, set `is_stale=True` on that source; merge into `AggregatedDataBundle`; write each source's data to `aggregated_market_data` table; call `CacheService.set_aggregated`; return bundle
    - `_merge_with_fallbacks(results)` — iterate 3 results; substitute mock where `isinstance(result, Exception)`; return `AggregatedDataBundle` with all three top-level fields populated
    - _Requirements: 3.1, 3.5, 9.1, 9.2, 9.3_

  - [x] 5.3 Write property tests for AggregationService (P6, P9)
    - **Property 6: Data Aggregation Completeness Under Partial Failure**
    - **Property 9: Cache Hit Idempotence**
    - **Validates: Requirements 3.1, 3.5, 9.2, 9.3**
    - In `backend/tests/test_aggregation_service.py`, use `@given(st.lists(st.booleans(), min_size=3, max_size=3))` to represent the 8 availability combinations; mock each service to either return valid data or raise `Exception`; assert returned `AggregatedDataBundle` always has `listings`, `demographics`, `market_metrics` non-null and that failed sources are marked `is_stale=True`
    - Mock Redis to return a pre-seeded bundle; assert external API call counters remain 0 on repeated calls within TTL

- [x] 6. CacheService
  - [x] 6.1 Implement CacheService
    - Create `backend/app/services/cache_service.py` with `CacheService` wrapping async Redis
    - `get_aggregated(location_id)` — key `aggregated:{location_id}`; deserialize JSON to `AggregatedDataBundle`; return `None` on miss
    - `set_aggregated(location_id, data)` — serialize to JSON; `SET ... EX {CACHE_TTL_SECONDS}`
    - `get_report(report_id)` — key `report:{report_id}`; TTL 24 h
    - `set_report(report_id, data)` — serialize `ReportResponse` to JSON; TTL 86400 s
    - `invalidate(location_id)` — `DEL aggregated:{location_id}`
    - Log and swallow `RedisError` (non-fatal); re-raise only `CacheError` wrapper
    - _Requirements: 3.5, 9.3_

  - [x] 6.2 Write property tests for CacheService (P9)
    - **Property 9: Cache Hit Idempotence**
    - **Validates: Requirements 3.5, 9.3**
    - In `backend/tests/test_cache_service.py`, use `@given(st.uuids(), st.fixed_dictionaries({...}))` to generate location IDs and `AggregatedDataBundle` fixtures; mock `aioredis.Redis`; assert `get_aggregated(set(id, data)); get_aggregated(id) == data`; assert calling `get_aggregated` after TTL expiry (mock `GET` to return `None`) yields `None`

- [x] 7. GeminiService and AI report generation
  - [x] 7.1 Implement GeminiService
    - Create `backend/app/services/gemini_service.py`
    - `build_prompt(location, data)` — construct prompt injecting `location` context + JSON block containing `market_metrics`, `demographics`, `listings` (serialized via `model_dump()`); instruct model to produce all 6 sections in Markdown with headers matching `REQUIRED_SECTIONS`; return prompt string
    - `parse_sections(response_text)` — use regex anchored to `## {SectionName}` headers to extract each section's content; return `dict[str, str]`
    - `validate_sections(sections)` — return list of section names missing from dict or with empty stripped content
    - `generate_report(location, data)` — call `genai.GenerativeModel("gemini-1.5-pro").generate_content(prompt)`; run `validate_sections`; if missing sections: re-prompt once with correction instruction `"The following sections were missing: {missing}. Please regenerate them."`; on `GeminiError`/timeout: return 5 populated sections + `ai_summary = "AI Summary temporarily unavailable. Please retry."`
    - _Requirements: 3.2, 3.3, 3.6, 3.7, 11.1, 11.2, 11.3_

  - [x] 7.2 Write property tests for GeminiService (P7, P10, P24)
    - **Property 7: Gemini Response Section Parsing**
    - **Property 10: Partial Report on Gemini Failure**
    - **Property 24: Gemini Prompt Data Completeness**
    - **Validates: Requirements 3.3, 3.7, 11.1, 11.2**
    - In `backend/tests/test_gemini_service.py`:
      - `@given(st.text())` for `parse_sections` — if all 6 headers present, assert 6 non-empty keys returned; if any header absent, assert `validate_sections` returns non-empty list containing that name
      - `@given(aggregated_data_strategy())` for `build_prompt` — assert JSON block contains all three data categories and all 6 section names appear in the prompt string
      - Mock `genai` to raise `Exception`; use `@given(aggregated_data_strategy())` to assert `ai_summary` is non-empty placeholder string

- [x] 8. ReportService and report orchestration
  - [x] 8.1 Implement ReportService
    - Create `backend/app/services/report_service.py` — `ReportService.create_report(user_id, location_id, db)`
    - Step 1: load `Location` by `location_id`; raise `LocationNotFoundError` if absent
    - Step 2: `CacheService.get_aggregated(location_id)` — if miss, call `AggregationService.aggregate_for_location`; set cache
    - Step 3: `GeminiService.generate_report(location, aggregated_data)` — enforce 30 s timeout via `asyncio.wait_for`; on `asyncio.TimeoutError` raise `ReportGenerationError` with message `"Report generation timed out"`
    - Step 4: call `generate_share_token()`; insert `Report` row with all 6 sections and extracted metrics; return `ReportResponse`
    - Create `backend/app/services/pdf_service.py` — `PDFService.generate(report)` renders `backend/templates/report.html` via Jinja2 with branding header, location name, generation date, all 6 sections; calls `weasyprint.HTML(string=html).write_pdf()`; returns `bytes`
    - Create `backend/templates/report.html` HTML template with Cotality Intelligence branding
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6, 3.7_

  - [x] 8.2 Implement reports router
    - Create `backend/app/routers/reports.py`:
      - `POST /reports` (JWT) — call `ReportService.create_report`; return `ReportResponse`
      - `GET /reports/{id}` (JWT, owner check) — load report; 404 if `is_deleted`; 403 if not owner; return `ReportResponse`; cache result for 24 h
      - `DELETE /reports/{id}` (JWT, owner check) — set `is_deleted=True`; invalidate cache; return 204
      - `GET /reports/share/{token}` (no auth) — load by `share_token`; 404 if not found or deleted; return `ReportResponse`
      - `GET /reports/{id}/export/pdf` (JWT) — call `PDFService.generate`; stream as `application/pdf` with `Content-Disposition: attachment; filename="report-{id}.pdf"`
    - _Requirements: 3.4, 4.1, 4.5, 4.6, 5.1, 5.3, 6.4_

  - [x] 8.3 Write property tests for PDFService (P15)
    - **Property 15: PDF Content Completeness**
    - **Validates: Requirements 5.2**
    - In `backend/tests/test_pdf_service.py`, use `@given(report_response_strategy())` to generate random `ReportResponse` fixtures; call `PDFService.generate(report)`; extract text from PDF bytes (using `pdfminer` or regex on raw bytes); assert presence of `display_name`, all 6 section headings, `"Cotality Intelligence"`, and `created_at` date string

  - [x] 8.4 Write integration tests for report generation pipeline (P10, P11)
    - **Property 10: Partial Report on Gemini Failure**
    - **Property 11: Report Rendering Completeness**
    - **Validates: Requirements 3.7, 4.1, 4.2**
    - In `backend/tests/test_report_service.py`, use `@given(location_strategy())` to mock `GeminiService.generate_report` to raise `GeminiError`; assert returned `ReportResponse` has non-empty `ai_summary` placeholder and all other 5 sections populated
    - Use `@given(report_response_strategy())` and assert all 6 section keys are non-empty strings

- [x] 9. Dashboard and Pro tier — backend
  - [x] 9.1 Implement dashboard router
    - Create `backend/app/routers/dashboard.py`:
      - `GET /dashboard/reports` (JWT) — query `reports` WHERE `user_id=current_user.id AND is_deleted=False` ORDER BY `created_at DESC` LIMIT 20; return list of `DashboardReport`
      - `POST /dashboard/saved-locations` (JWT + `require_pro`) — upsert `SavedLocation`; return `SavedLocationResponse`
      - `GET /dashboard/saved-locations` (JWT + `require_pro`) — return list of saved locations with location details
      - `DELETE /dashboard/saved-locations/{id}` (JWT + `require_pro`) — delete record; 404 if not owned by current user
      - `GET /dashboard/analytics` (JWT + `require_pro`) — join saved locations with latest report per location; extract `roi_estimate` and `rental_yield`; return list sorted by `roi_estimate` descending
    - _Requirements: 6.1, 6.2, 6.4, 7.1, 7.2, 7.4, 7.5_

  - [x] 9.2 Implement watchlist router
    - Create `backend/app/routers/watchlist.py`:
      - `POST /watchlist` (JWT + `require_pro`) — insert `WatchlistEntry`; return entry
      - `GET /watchlist` (JWT + `require_pro`) — join with last 12 `aggregated_market_data` records per location for sparkline data; return `list[WatchlistEntryResponse]`
      - `DELETE /watchlist/{id}` (JWT + `require_pro`) — delete entry owned by current user
    - _Requirements: 7.3, 7.5_

  - [x] 9.3 Write property tests for dashboard queries (P16, P17, P18, P19, P20)
    - **Property 16: Dashboard Ordering and Limit**
    - **Property 17: Soft-Delete Visibility**
    - **Property 18: Saved Location Round-Trip**
    - **Property 19: Investment Analytics Ordering**
    - **Property 20: Pro Feature Gate**
    - **Validates: Requirements 6.1, 6.4, 7.2, 7.4, 7.5**
    - In `backend/tests/test_dashboard_queries.py`, use `@given(st.lists(report_fixture_strategy(), min_size=0, max_size=50))` — assert result length ≤ 20 and results are strictly ordered by `created_at` descending
    - Generate reports with random `is_deleted` flags; assert deleted reports never appear in response
    - Use `@given(st.uuids())` for saved-location round-trip: save → list → assert `location_id` in response
    - Use `@given(st.lists(analytics_fixture(), min_size=1))` for analytics: assert descending `roi_estimate` order
    - Mock JWT to use `tier="regular"`; assert all Pro endpoints return 403

- [x] 10. Checkpoint — backend complete
  - Ensure all backend tests pass: `cd backend && pytest tests/ -v`
  - Ensure Alembic migration applies cleanly against a fresh PostgreSQL container: `alembic upgrade head`
  - Ask the user if any backend behavior needs adjustment before proceeding to the frontend.

- [x] 11. NextAuth.js configuration and auth pages
  - [x] 11.1 Configure NextAuth.js
    - Create `frontend/src/lib/auth.ts` with `authOptions`: `GoogleProvider` (using `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`), `CredentialsProvider` (POST to `BACKEND_URL/auth/login`); `jwt` callback stores `backendToken` and `tier`; `session` callback exposes `session.backendToken` and `session.user.tier`
    - Create `frontend/src/app/api/auth/[...nextauth]/route.ts` exporting `{ GET, POST }` from `NextAuth(authOptions)`
    - Update `frontend/src/app/(app)/layout.tsx` to call `getServerSession(authOptions)`; redirect to `/login?callbackUrl=...` if no session
    - _Requirements: 2.1, 2.4, 2.5, 2.6_

  - [x] 11.2 Implement login and register pages
    - Create `frontend/src/app/(auth)/login/page.tsx` — email/password form calling `signIn("credentials", {...})`; Google OAuth button calling `signIn("google")`; link to `/register`; display error on failed auth
    - Create `frontend/src/app/(auth)/register/page.tsx` — email/password/name form POSTing to FastAPI `POST /auth/register` via `apiPost`; on success, call `signIn("credentials")`; client-side validation: email format, password ≥ 8 chars
    - _Requirements: 2.1, 2.2, 2.3, 2.6_

- [x] 12. Location search component and report new page
  - [x] 12.1 Implement LocationSearch component
    - Create `frontend/src/components/location-search.tsx`
    - Render `<Input>` with `onChange` handler debounced 300 ms via `setTimeout`/`clearTimeout`
    - On debounce fire: call `apiGet<AutocompleteResponse>("/locations/autocomplete?q={query}", session)` (no auth for this endpoint)
    - Render dropdown of ≤ 8 results showing `suburb`, `city`, `state`; on item click call `onLocationSelect(location)` and clear dropdown
    - Display "Location not in Australia" if `country_code != "AU"`; display error state if API call fails
    - Accept props: `onLocationSelect`, `placeholder`, `autoFocus`
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 12.2 Implement report/new page
    - Refactor `frontend/src/app/(app)/report/new/page.tsx`
    - Render `<LocationSearch>` component; on selection store `selectedLocation` in state
    - "Generate Report" button: POST to FastAPI `POST /reports` with `{location_id: selectedLocation.id}` via `apiPost`; on success redirect to `/report/{id}`; show loading spinner during generation; show error toast on failure with retry button
    - _Requirements: 3.1, 3.6_

- [x] 13. Report section components
  - [x] 13.1 Implement MarketOverview and NeighbourhoodInsights section components
    - Create `frontend/src/components/report-sections/market-overview.tsx` — render `content` as markdown via `<ReactMarkdown>`; render stat cards for `median_price`, `price_appreciation`, `rental_yield`, `days_on_market`, `roi_estimate` using shadcn `Card` with prominent typography
    - Create `frontend/src/components/report-sections/neighbourhood-insights.tsx` — render `content` as markdown
    - Both components accept `{ content: string }` and use skeleton loaders while loading
    - _Requirements: 4.1, 4.2, 11.4_

  - [x] 13.2 Implement Demographics, InvestmentIntelligence, and AISummary section components
    - Create `frontend/src/components/report-sections/demographics.tsx` — render markdown content
    - Create `frontend/src/components/report-sections/investment-intelligence.tsx` — render markdown content
    - Create `frontend/src/components/report-sections/ai-summary.tsx` — render markdown with sub-sections: Market Summary, Investment Recommendation, Risk Indicators, Opportunities; skeleton loader state
    - All components accept `{ content: string }` and render via `<ReactMarkdown>`
    - _Requirements: 4.1, 11.3, 11.4_

  - [x] 13.3 Implement ComparableProperties section component
    - Create `frontend/src/components/report-sections/comparable-properties.tsx`
    - Render sortable table with columns: `address`, `price`, `beds`, `baths`, `sqft`, `listing_type`; sort by clicking column header (client-side)
    - If `isPro=true`: render filter controls for `propertyType`, `priceMin`/`priceMax`, `bedsMin`, `bathsMin`; filter is applied client-side against `properties` array on filter change; show "No matching properties" when result is empty
    - If `isPro=false`: render table with no filters; render `<ProUpgradePrompt featureName="Advanced Filters" />` adjacent to the filter area
    - Accept props: `{ properties: PropertyListing[], isPro: boolean, onFilterChange?: (filters: PropertyFilters) => void }`
    - _Requirements: 4.3, 8.1, 8.2, 8.3, 8.4_

  - [x] 13.4 Write fast-check property tests for ComparableProperties filters (P12, P21)
    - **Property 12: Comparable Properties Table Integrity**
    - **Property 21: Comparable Properties Filter Correctness**
    - **Validates: Requirements 4.3, 8.2, 8.3**
    - In `frontend/src/__tests__/comparable-properties.test.ts`, use `fc.array(propertyListingArbitrary)` to render `<ComparableProperties>` and assert exactly N table rows rendered; use `fc.record({propertyType, priceMin, priceMax, bedsMin, bathsMin})` as filters and assert filtered result contains exactly those listings satisfying all active predicates simultaneously

- [x] 14. Report view page and share functionality
  - [x] 14.1 Implement report/[id] page
    - Refactor `frontend/src/app/(app)/report/[id]/page.tsx`
    - Fetch `GET /reports/{id}` via `apiGet<ReportResponse>` using session JWT; show 404 if not found; show read-only mode (no edit/delete buttons) if `report.user_id != session.user.id`
    - Render all 6 section components; render stat cards for key metrics
    - "Share" button: construct `{NEXTAUTH_URL}/share/{share_token}`, copy to clipboard, show toast "Link copied!"
    - "Export PDF" button (authenticated owner only): call `GET /reports/{id}/export/pdf` via `apiGet` with JWT; trigger browser download; show error toast on failure
    - "Delete" button (owner only): call `apiDelete`; on success redirect to `/dashboard`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.3, 6.4_

  - [x] 14.2 Implement share/[token] page
    - Create `frontend/src/app/share/[token]/page.tsx`
    - Fetch `GET /reports/share/{token}` (no auth needed); render all 6 section components in read-only mode (no share/delete/export buttons shown)
    - Show 404 page if token not found
    - _Requirements: 4.5, 4.6_

- [x] 15. Dashboard — Regular and Pro tier
  - [x] 15.1 Implement dashboard page with regular features
    - Refactor `frontend/src/app/(app)/dashboard/page.tsx`
    - Fetch `GET /dashboard/reports` via `apiGet`; render list of up to 20 `ReportCard` components
    - Create `frontend/src/components/dashboard/report-card.tsx` — display location name, `created_at` formatted date, `median_price`, link to `/report/{id}`; delete button calling `apiDelete` with optimistic UI removal (no page reload)
    - Show empty-state component with "Generate your first report" CTA when list is empty
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 15.2 Implement Pro dashboard panels
    - Create `frontend/src/components/dashboard/saved-locations.tsx` — fetch `GET /dashboard/saved-locations`; render list with location name and "Generate Report" button (navigates to `/report/new?location_id={id}`); show `<ProUpgradePrompt>` if `session.user.tier != "pro"`
    - Create `frontend/src/components/dashboard/watchlist-panel.tsx` — fetch `GET /watchlist`; render each entry with location name and Recharts `<Sparkline>` showing last 12 median price data points; show `<ProUpgradePrompt>` for non-pro users
    - Create `frontend/src/components/dashboard/investment-analytics.tsx` — fetch `GET /dashboard/analytics`; render ranked table with columns: Location, ROI Estimate, Rental Yield; show `<ProUpgradePrompt>` for non-pro users
    - Create `frontend/src/components/pro-upgrade-prompt.tsx` — modal/inline component accepting `featureName: string`; display upgrade copy and button
    - Update dashboard page to render all 4 panels (3 Pro panels gated behind tier check)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 15.3 Implement pro/watchlist and pro/analytics pages
    - Create `frontend/src/app/(app)/pro/watchlist/page.tsx` — full-page watchlist view; add location to watchlist via `apiPost` to `POST /watchlist`; delete entry; all gated by `require_pro` redirect
    - Create `frontend/src/app/(app)/pro/analytics/page.tsx` — full investment analytics page with ranked table; gated by `require_pro` redirect
    - _Requirements: 7.3, 7.4, 7.5_

- [x] 16. Checkpoint — end-to-end integration
  - Verify Docker Compose starts all 4 services with `docker compose up --build`
  - Verify Alembic migrations run automatically before FastAPI accepts requests
  - Verify login (Google OAuth + credentials), report generation, share link, PDF export work end-to-end
  - Ask the user if any integration issues need resolving before proceeding.

- [x] 17. Environment variable startup validation
  - [x] 17.1 Implement Pydantic Settings with strict validation
    - Update `backend/app/config.py` — use `pydantic_settings.BaseSettings`; mark all required env vars as fields with no default; include `model_config = SettingsConfigDict(env_file=".env")`; ensure Pydantic raises `ValidationError` on startup if any required variable is missing
    - Add startup lifespan event in `backend/app/main.py` that instantiates `Settings()` immediately (not lazily) so missing env vars fail fast at container start
    - _Requirements: 10.3_

  - [x] 17.2 Write property tests for Settings validation (P23)
    - **Property 23: Environment Variable Startup Validation**
    - **Validates: Requirements 10.3**
    - In `backend/tests/test_config.py`, enumerate all required env var names; use `@given(st.sets(st.sampled_from(REQUIRED_VARS), min_size=1))` to generate subsets of missing vars; for each subset mock `os.environ` to omit those vars; assert `Settings()` raises `ValidationError` containing at least one missing var name

- [x] 18. Documentation
  - [x] 18.1 Write README.md
    - Create `e:/realestate/realestate-platform-v2/README.md` covering: project overview, architecture diagram (ASCII), prerequisites (Docker, Docker Compose, Node 20, Python 3.12), quick-start (`cp .env.example .env`, fill vars, `docker compose up --build`), available services and ports, running tests (`pytest` for backend, `npm test` for frontend), environment variable reference table
    - _Requirements: 10.1_

  - [x] 18.2 Write how-to-get-apis.md
    - Create `e:/realestate/realestate-platform-v2/how-to-get-apis.md` covering: how to obtain Domain API credentials (domain.com.au developer portal), Google Gemini API key (Google AI Studio), Google OAuth client ID/secret (Google Cloud Console), and notes on ABS and data.gov.au (public, no key needed)
    - _Requirements: 10.1_

- [x] 19. Final checkpoint — all tests pass
  - Run `cd backend && pytest tests/ -v --tb=short` and confirm all tests pass
  - Run `cd frontend && npm test -- --run` and confirm all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; core functionality is complete without them
- Each task references specific requirements for traceability
- Property tests reference their design document property number (P1–P24) for traceability
- The backend uses Hypothesis for Python property tests (`@given`, `@settings(max_examples=100)`)
- The frontend uses fast-check for TypeScript property tests (`fc.assert(fc.property(...))`)
- Checkpoints at tasks 10, 16, and 19 ensure incremental validation before proceeding
- The Docker Compose `backend` command runs `alembic upgrade head` before `uvicorn` starts — migrations are automatic
- Existing MVP at `e:/realestate/platform` is the migration source; no existing files are deleted during scaffolding

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["2.3", "3.1", "5.1", "6.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "4.1", "5.2", "6.2", "7.1"] },
    { "id": 4, "tasks": ["3.4", "3.5", "4.2", "5.3", "7.2", "8.1"] },
    { "id": 5, "tasks": ["8.2", "9.1", "9.2", "11.1"] },
    { "id": 6, "tasks": ["8.3", "8.4", "9.3", "11.2", "12.1"] },
    { "id": 7, "tasks": ["12.2", "13.1", "13.2", "13.3", "17.1"] },
    { "id": 8, "tasks": ["13.4", "14.1", "14.2", "15.1", "17.2"] },
    { "id": 9, "tasks": ["15.2", "15.3"] },
    { "id": 10, "tasks": ["18.1", "18.2"] }
  ]
}
```
