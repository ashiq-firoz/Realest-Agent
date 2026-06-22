"""
AmenitiesService — real neighbourhood amenity data from OpenStreetMap (Overpass API).

Free, no API key. Uses the latitude/longitude already resolved for every location to
count nearby schools, hospitals, transport, supermarkets, parks and dining within a
radius, and derives simple walkability/lifestyle proxy scores for the Neighbourhood
Insights section. Falls back to a neutral (zeroed) snapshot on any failure.
"""
import logging
from datetime import date

import httpx

from app.config import settings
from app.schemas.geography import GeographyMetadata
from app.schemas.location import LocationSummary
from app.schemas.report import AmenitiesSnapshot

logger = logging.getLogger(__name__)

DEFAULT_RADIUS_M = 1500


def _unavailable(location: LocationSummary | None = None, radius: int = DEFAULT_RADIUS_M) -> AmenitiesSnapshot:
    """Neutral snapshot used when Overpass is unreachable or returns nothing."""
    return AmenitiesSnapshot(
        radius_m=radius,
        source="unavailable",
        metadata=GeographyMetadata(
            geography_type="point",
            geography_id=(location.display_name if location else "unknown"),
            source="osm_unavailable",
            as_of_date=date.today().isoformat(),
        ),
    )


class AmenitiesService:
    OVERPASS_URL = getattr(settings, "OVERPASS_URL", "https://overpass-api.de/api/interpreter")

    def _build_query(self, lat: float, lon: float, radius: int) -> str:
        a = f"(around:{radius},{lat},{lon})"
        return (
            "[out:json][timeout:25];"
            "("
            f'nwr["amenity"~"^(school|hospital|pharmacy|cafe|restaurant)$"]{a};'
            f'nwr["shop"="supermarket"]{a};'
            f'nwr["leisure"="park"]{a};'
            f'nwr["railway"="station"]{a};'
            f'nwr["public_transport"="station"]{a};'
            f'nwr["highway"="bus_stop"]{a};'
            ");"
            "out tags center;"
        )

    @staticmethod
    def _count(elements: list[dict]) -> AmenitiesSnapshot:
        schools = hospitals = pharmacies = supermarkets = parks = 0
        train_stations = bus_stops = cafes_restaurants = 0

        for el in elements:
            tags = el.get("tags", {}) or {}
            amenity = tags.get("amenity")
            if amenity == "school":
                schools += 1
            elif amenity == "hospital":
                hospitals += 1
            elif amenity == "pharmacy":
                pharmacies += 1
            elif amenity in ("cafe", "restaurant"):
                cafes_restaurants += 1
            if tags.get("shop") == "supermarket":
                supermarkets += 1
            if tags.get("leisure") == "park":
                parks += 1
            if tags.get("railway") == "station" or tags.get("public_transport") == "station":
                train_stations += 1
            if tags.get("highway") == "bus_stop":
                bus_stops += 1

        walkability = min(
            100,
            int(
                schools * 6 + supermarkets * 8 + pharmacies * 5
                + cafes_restaurants * 1.5 + bus_stops * 1
                + train_stations * 12 + parks * 3 + hospitals * 5
            ),
        )
        lifestyle = min(
            100,
            int(parks * 6 + cafes_restaurants * 3 + supermarkets * 5 + schools * 3),
        )

        return AmenitiesSnapshot(
            schools=schools,
            hospitals=hospitals,
            pharmacies=pharmacies,
            supermarkets=supermarkets,
            parks=parks,
            train_stations=train_stations,
            bus_stops=bus_stops,
            cafes_restaurants=cafes_restaurants,
            walkability_score=walkability,
            lifestyle_score=lifestyle,
        )

    async def fetch_amenities(
        self,
        location: LocationSummary,
        radius: int = DEFAULT_RADIUS_M,
    ) -> AmenitiesSnapshot:
        """Query Overpass for nearby amenities. Never raises — returns a neutral snapshot on failure."""
        lat, lon = location.latitude, location.longitude
        if not lat or not lon:
            return _unavailable(location, radius)

        query = self._build_query(lat, lon, radius)
        # Overpass rejects requests without a descriptive User-Agent (HTTP 406).
        headers = {"User-Agent": "CotalityIntelligence/1.0 (real-estate-report)"}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.OVERPASS_URL, data={"data": query}, headers=headers)
                resp.raise_for_status()
                elements = resp.json().get("elements", [])
        except (httpx.HTTPError, ValueError, Exception) as exc:  # noqa: BLE001
            logger.warning("Overpass error for %s: %s", location.display_name, exc)
            return _unavailable(location, radius)

        snapshot = self._count(elements)
        snapshot.radius_m = radius
        snapshot.metadata = GeographyMetadata(
            geography_type="point",
            geography_id=location.display_name,
            source="openstreetmap",
            as_of_date=date.today().isoformat(),
        )
        return snapshot
