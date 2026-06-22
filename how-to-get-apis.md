# How to Get APIs

Cotality Intelligence runs on **free** Australian data sources. Only the Gemini key is
strictly required; everything else is keyless or has a graceful mock fallback.

## Data sources at a glance

| Report data | Source | API key? |
|---|---|---|
| AI synthesis (all narrative sections) | Google Gemini | **Required** |
| Location autocomplete / geocoding | Nominatim (OpenStreetMap) + local suburb dataset | No |
| Demographics (population, median age, household income) + median rent | ABS Data API — Census 2021 *Postal Area* (`C21_G01_POA`, `C21_G02_POA`) | No |
| Price appreciation (YoY, capital-city) | ABS Data API — Residential Property Price Index (`RPPI`) | No |
| Neighbourhood amenities (schools, hospitals, transport, supermarkets, parks, walkability) | OpenStreetMap Overpass API | No |
| Comparable properties (address, beds, baths, type) | PropertyLens | Optional (free tier) |

> **Note on price metrics:** No free API publishes live suburb-level median **sale**
> price / rental yield / days-on-market. These are AI-estimated from the real comps,
> demographics and price-index trend, and are clearly labelled as estimates in the
> report. The comparable listings are real but do **not** include sale prices.

## 1. Google Gemini API (required)

1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in and create an API key.
3. Set it as `GEMINI_API_KEY` in your `.env`.

## 2. ABS Data API (no key)

The Australian Bureau of Statistics [Data API](https://data.api.abs.gov.au) is free and
keyless (SDMX-JSON). We query Census 2021 Postal Area tables by postcode and the RPPI
for capital-city price trends. Override `ABS_API_BASE` only if needed.

## 3. OpenStreetMap Overpass API (no key)

Neighbourhood amenities are counted via the [Overpass API](https://overpass-api.de/).
No key required; requests must send a descriptive `User-Agent` (handled in code) and are
cached in Redis. Override `OVERPASS_URL` to use a mirror if desired.

## 4. Nominatim (no key)

Used for suburb autocomplete/geocoding fallback. No key, but respect the
[usage policy](https://operations.osmfoundation.org/policies/nominatim/); results are cached.

## 5. PropertyLens (optional, free tier)

Provides real comparable property listings.

1. Sign up at [PropertyLens](https://app.propertylens.au/) and create an API key.
2. Set it as `PROPERTYLENS_API_KEY` in your `.env`.

Free tier notes: the search endpoint returns addresses/beds/baths/type **without prices**
and is **heavily limited — about 5 requests per day** (and 2/min), so it is effectively
demo-only. Redis caching keeps live calls rare. If the key is unset or the limit is hit,
the **Comparable Properties** section shows an empty state (no fake placeholder rows).
For production-grade comparables you would need a paid property-data API (e.g. Domain or
PropertyLens paid tiers).

## 6. Domain API (dropped)

Domain's listings `_search` endpoint requires a paid OAuth plan (returns 403 on the free
project key), so it is no longer used. Leave `DOMAIN_API_KEY` blank.

## 7. Google OAuth (optional)

For "Continue with Google" sign-in:

1. In the [Google Cloud Console](https://console.cloud.google.com/), create OAuth 2.0
   credentials (Web application).
2. Add `http://localhost:3000/api/auth/callback/google` as an authorized redirect URI.
3. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in your `.env`.
