# Implementation Plan: Real Estate Intelligence Platform Tasks

The goal is to complete the pending tasks outlined in `.kiro/specs/real-estate-intelligence-platform/tasks.md`. Based on our repository analysis, the backend scaffolding and core business logic are mostly in place, but several tests are missing or failing, and the frontend/documentation portions are entirely pending.

Given the magnitude of the work, this plan structures the execution into logical phases.

## Open Questions

> [!WARNING]
> This is a large scope of work spanning backend testing, full Next.js frontend implementation, and project documentation. Are there any specific parts (e.g., frontend components or backend tests) you would like me to prioritize first, or should I proceed sequentially starting with fixing the failing backend tests?

## Proposed Changes

### Phase 1: Backend Stabilization & Missing Tests
*Fix currently failing tests and implement the missing property tests.*

#### [MODIFY] `backend/tests/test_pdf_service.py`
- Update the patching of `weasyprint` so it works with dynamic imports inside the `generate` function (`patch(..., create=True)` or direct class patching).
- Fix `AttributeError`.

#### [MODIFY] `backend/tests/test_auth_deps.py`
- Address the 5 failing tests related to JWT logic and Pro feature gating.

#### [NEW] `backend/tests/test_report_service.py`
- Implement Task 8.4: Property tests for report generation pipeline (P10, P11) verifying partial report generation and content completeness.

#### [NEW] `backend/tests/test_dashboard_queries.py`
- Implement Task 9.3: Property tests (P16-P20) for dashboard limits, soft-delete visibility, and pro-feature gating.

#### [MODIFY] `backend/app/config.py` & [NEW] `backend/tests/test_config.py`
- Implement Tasks 17.1 & 17.2: Ensure Pydantic `BaseSettings` raises `ValidationError` on missing env vars, and write corresponding property tests (P23).

---

### Phase 2: Frontend Auth & Search
*Configure NextAuth and build the basic user flows.*

#### [NEW] `frontend/src/lib/auth.ts` & NextAuth Route
- Task 11.1: NextAuth.js configuration using GoogleProvider and CredentialsProvider.

#### [NEW] `frontend/src/app/(auth)/login/page.tsx` & `register/page.tsx`
- Task 11.2: Implement login and registration forms using shadcn components and API integrations.

#### [NEW] `frontend/src/components/location-search.tsx`
- Task 12.1: Implement debounced Nominatim location search component.

#### [MODIFY] `frontend/src/app/(app)/report/new/page.tsx`
- Task 12.2: Refactor report creation flow and integrate the `LocationSearch` component.

---

### Phase 3: Frontend Report Rendering
*Build all components that render the generated report and associated property tests.*

#### [NEW] `frontend/src/components/report-sections/*.tsx`
- Tasks 13.1, 13.2, 13.3: Implement the 6 report section components (MarketOverview, Demographics, ComparableProperties, etc.).

#### [NEW] `frontend/src/__tests__/comparable-properties.test.ts`
- Task 13.4: Write fast-check property tests for comparable properties table integrity and filter correctness.

#### [MODIFY] `frontend/src/app/(app)/report/[id]/page.tsx` & `share/[token]/page.tsx`
- Tasks 14.1, 14.2: Build the full report view page and the unauthenticated share page.

---

### Phase 4: Frontend Dashboard & Pro Features
*Implement the dashboard layout and Pro tier gates.*

#### [MODIFY] `frontend/src/app/(app)/dashboard/page.tsx` & Dashboard Components
- Tasks 15.1, 15.2: Build the regular dashboard features and Pro panel placeholders.

#### [NEW] `frontend/src/app/(app)/pro/watchlist/page.tsx` & `analytics/page.tsx`
- Task 15.3: Build the full-page Pro views.

---

### Phase 5: Documentation
*Finish up the repository deliverables.*

#### [NEW] `README.md` & `how-to-get-apis.md`
- Tasks 18.1, 18.2: Write comprehensive user instructions.

## Verification Plan

### Automated Tests
- `pytest tests/ -v` on the backend until all tests pass and coverage is optimal.
- `npm test -- --run` on the frontend to ensure all fast-check properties hold.

### Manual Verification
- Start `docker compose up --build`.
- Run through login, location search, report generation, sharing, and exporting flows manually.
