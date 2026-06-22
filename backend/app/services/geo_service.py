"""
GeoService — Australian location autocomplete via local suburbs dataset.

Uses a curated dataset of Australian suburbs/cities for instant prefix matching.
Falls back to Nominatim for queries that don't match any local entry.
"""
import logging
import uuid
from typing import Optional

import httpx

from app.schemas.location import LocationSummary
from app.services.au_suburbs_data import AU_SUBURBS

logger = logging.getLogger(__name__)


class GeocodeError(Exception):
    """Raised when geocoding fails."""


# ---------------------------------------------------------------------------
# Build a sorted index for fast prefix matching at module load time
# ---------------------------------------------------------------------------

_SUBURB_INDEX: list[tuple[str, LocationSummary]] = []

for _suburb, _city, _state, _postcode, _lat, _lon in AU_SUBURBS:
    _display = (
        f"{_suburb}, {_city}, {_state} {_postcode}"
        if _suburb != _city and _suburb != f"{_city} CBD"
        else f"{_city}, {_state} {_postcode}"
    )
    _loc = LocationSummary(
        id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{_suburb}-{_postcode}")),
        display_name=_display,
        suburb=_suburb if _suburb != _city else None,
        city=_city,
        state=_state,
        postcode=_postcode,
        country_code="AU",
        latitude=_lat,
        longitude=_lon,
    )
    # Store lowered suburb name for matching, plus the full LocationSummary
    _SUBURB_INDEX.append((_suburb.lower(), _loc))

# Also index by city name and postcode for those searches
_seen_cities: set[str] = set()
for _suburb, _city, _state, _postcode, _lat, _lon in AU_SUBURBS:
    _city_key = f"{_city}-{_state}".lower()
    if _city_key not in _seen_cities:
        _seen_cities.add(_city_key)
        _display = f"{_city}, {_state} {_postcode}"
        _loc = LocationSummary(
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{_city}-{_state}-{_postcode}")),
            display_name=_display,
            suburb=None,
            city=_city,
            state=_state,
            postcode=_postcode,
            country_code="AU",
            latitude=_lat,
            longitude=_lon,
        )
        _SUBURB_INDEX.append((_city.lower(), _loc))

# Index by postcode as well
_seen_postcodes: set[str] = set()
for _suburb, _city, _state, _postcode, _lat, _lon in AU_SUBURBS:
    if _postcode not in _seen_postcodes:
        _seen_postcodes.add(_postcode)
        _display = f"{_postcode} — {_city}, {_state}"
        _loc = LocationSummary(
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"pc-{_postcode}-{_city}")),
            display_name=_display,
            suburb=None,
            city=_city,
            state=_state,
            postcode=_postcode,
            country_code="AU",
            latitude=_lat,
            longitude=_lon,
        )
        _SUBURB_INDEX.append((_postcode, _loc))

# Sort for consistent ordering
_SUBURB_INDEX.sort(key=lambda x: x[0])


class GeoService:
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    USER_AGENT = "CotalityIntelligence/1.0"

    async def autocomplete(self, query: str) -> list[LocationSummary]:
        """
        Prefix-match against a local Australian suburbs dataset.
        Returns ≤ 8 results. Falls back to Nominatim for unmatched queries.
        """
        q = query.strip().lower()
        if not q:
            return []

        # Prefix match against the local index
        matches: list[LocationSummary] = []
        seen_display: set[str] = set()

        for key, loc in _SUBURB_INDEX:
            if key.startswith(q):
                if loc.display_name not in seen_display:
                    seen_display.add(loc.display_name)
                    matches.append(loc)
                    if len(matches) >= 8:
                        break

        if matches:
            return matches

        # If no local matches, try substring matching (e.g. "kilda" → "St Kilda")
        for key, loc in _SUBURB_INDEX:
            if q in key:
                if loc.display_name not in seen_display:
                    seen_display.add(loc.display_name)
                    matches.append(loc)
                    if len(matches) >= 8:
                        break

        if matches:
            return matches

        # Final fallback: Nominatim for obscure locations
        return await self._nominatim_search(query)

    async def get_location_by_id(self, location_id: str) -> LocationSummary | None:
        """Find a location by its ID in the local index."""
        for key, loc in _SUBURB_INDEX:
            if loc.id == location_id:
                return loc
        return None

    async def _nominatim_search(self, query: str) -> list[LocationSummary]:
        """Fallback: query Nominatim with countrycodes=au restriction."""
        params = {
            "q": query,
            "countrycodes": "au",
            "format": "jsonv2",
            "addressdetails": "1",
            "limit": "8",
        }
        headers = {"User-Agent": self.USER_AGENT}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(self.NOMINATIM_URL, params=params, headers=headers)
                resp.raise_for_status()
                raw_results = resp.json()
            except httpx.HTTPError as exc:
                logger.error("Nominatim request failed: %s", exc)
                raise GeocodeError(f"Geocoding service unavailable: {exc}") from exc

        sorted_results = sorted(
            raw_results,
            key=lambda r: float(r.get("importance", 0)),
            reverse=True,
        )

        locations = []
        for item in sorted_results[:8]:
            try:
                loc = self._parse_nominatim_result(item)
                if loc.country_code.upper() == "AU":
                    locations.append(loc)
            except Exception as exc:
                logger.warning("Skipping unparseable Nominatim result: %s", exc)
                continue

        return locations[:8]

    def _parse_nominatim_result(self, result: dict) -> LocationSummary:
        """Extract suburb, city, state, postcode, lat/lon from a Nominatim result."""
        address = result.get("address", {})

        suburb: Optional[str] = address.get("suburb") or address.get("city_district") or None

        city: str = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("county")
            or address.get("suburb")
            or (result.get("display_name") or "").split(",")[0].strip()
            or "Unknown"
        )

        state: str = address.get("state") or address.get("state_district") or "Unknown"
        postcode: Optional[str] = address.get("postcode") or None
        country_code: str = (address.get("country_code") or "au").upper()

        try:
            lat = float(result.get("lat", 0))
            lon = float(result.get("lon", 0))
        except (ValueError, TypeError):
            lat, lon = 0.0, 0.0

        place_id: str = str(result.get("place_id", "")) or str(uuid.uuid4())

        return LocationSummary(
            id=place_id,
            display_name=result.get("display_name") or city,
            suburb=suburb,
            city=city,
            state=state,
            postcode=postcode,
            country_code=country_code,
            latitude=lat,
            longitude=lon,
        )

    # Keep legacy method names for backward compatibility with tests
    def parse_nominatim_result(self, result: dict) -> LocationSummary:
        return self._parse_nominatim_result(result)

    def is_australian(self, location: LocationSummary) -> bool:
        """Return True iff country_code == 'AU'."""
        return location.country_code.upper() == "AU"
