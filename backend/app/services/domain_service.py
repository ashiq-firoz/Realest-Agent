# """
# DomainService — fetches Australian property listings from the Domain API.
# Falls back to mock data if the API is unavailable.
# """
# import logging
# from typing import Optional
# import httpx
# from app.config import settings
# from app.schemas.location import LocationSummary
# from app.schemas.report import PropertyListing

# logger = logging.getLogger(__name__)

# # Mock listings used as fallback when Domain API is unavailable
# MOCK_LISTINGS: list[PropertyListing] = [
#     PropertyListing(
#         address="1 Example St, Sydney NSW 2000",
#         price="$850,000",
#         price_numeric=850000,
#         beds=3,
#         baths=2.0,
#         sqft=180,
#         listing_type="sold",
#         property_type="house",
#         source="mock",
#     ),
#     PropertyListing(
#         address="2 Sample Ave, Melbourne VIC 3000",
#         price="$620,000",
#         price_numeric=620000,
#         beds=2,
#         baths=1.0,
#         sqft=95,
#         listing_type="active",
#         property_type="unit",
#         source="mock",
#     ),
#     PropertyListing(
#         address="3 Demo Rd, Brisbane QLD 4000",
#         price="$540,000",
#         price_numeric=540000,
#         beds=3,
#         baths=2.0,
#         sqft=150,
#         listing_type="active",
#         property_type="townhouse",
#         source="mock",
#     ),
# ]


# class ServiceUnavailableError(Exception):
#     """Raised when an external data service is unreachable."""


# class DomainService:
#     BASE_URL = "https://api.domain.com.au/v1"

#     def normalize_listing(self, raw: dict) -> PropertyListing:
#         """Normalize a raw Domain API listing dict into a canonical PropertyListing."""
#         price_raw = raw.get("price", {}) or {}
#         price_numeric = price_raw.get("displayPrice") if isinstance(price_raw, dict) else None
#         if isinstance(price_numeric, str):
#             # Strip formatting: "$850,000" -> 850000
#             price_numeric = int("".join(filter(str.isdigit, price_numeric)) or "0")

#         price_display = (
#             f"${price_numeric:,}" if isinstance(price_numeric, int) and price_numeric
#             else raw.get("price_display") or "Price on application"
#         )

#         details = raw.get("propertyDetails", {}) or {}
#         beds_raw = details.get("bedrooms") or raw.get("bedrooms", 0)
#         baths_raw = details.get("bathrooms") or raw.get("bathrooms", 0)

#         prop_type_raw = (details.get("propertyType") or raw.get("property_type", "house")).lower()
#         prop_type_map = {"apartment": "unit", "flat": "unit", "studio": "unit", "villa": "townhouse"}
#         prop_type = prop_type_map.get(prop_type_raw, prop_type_raw)
#         if prop_type not in ("house", "unit", "townhouse", "land", "other"):
#             prop_type = "other"

#         listing_type_raw = raw.get("saleMode") or raw.get("listing_type", "active")
#         listing_type_map = {"sold": "sold", "auction": "active", "forSale": "active", "forLease": "leased"}
#         listing_type = listing_type_map.get(listing_type_raw, "active")

#         return PropertyListing(
#             address=raw.get("addressParts", {}).get("displayAddress") or raw.get("address", "Unknown"),
#             price=price_display,
#             price_numeric=price_numeric if isinstance(price_numeric, int) else None,
#             beds=int(beds_raw or 0),
#             baths=float(baths_raw or 0),
#             sqft=details.get("landArea") or raw.get("sqft"),
#             listing_type=listing_type,
#             property_type=prop_type,
#             source="domain",
#         )

#     async def fetch_listings(self, location: LocationSummary) -> list[PropertyListing]:
#         """
#         Fetch property listings from Domain API for the given location.
#         Normalizes each listing into PropertyListing.
#         Returns list[PropertyListing]. Raises ServiceUnavailableError on HTTP failure.
#         """
#         if not settings.DOMAIN_API_KEY or settings.DOMAIN_API_KEY.startswith("<"):
#             logger.warning("Domain API key not configured; returning mock listings")
#             return []

#         params = {
#             "suburb": location.suburb or location.city,
#             "state": location.state,
#             "postcode": location.postcode or "",
#             "listingType": "Sale",
#             "pageSize": 20,
#         }
#         headers = {"X-Api-Key": settings.DOMAIN_API_KEY}

#         async with httpx.AsyncClient(timeout=10.0) as client:
#             try:
#                 resp = await client.get(
#                     f"{self.BASE_URL}/listings/residential/_search",
#                     params=params,
#                     headers=headers,
#                 )
#                 resp.raise_for_status()
#                 data = resp.json()
#                 listings = data if isinstance(data, list) else data.get("listings", [])
#                 return [self.normalize_listing(item) for item in listings[:20]]
#             except (httpx.HTTPError, Exception) as exc:
#                 logger.error("Domain API error: %s", exc)
#                 raise ServiceUnavailableError(f"Domain API unavailable: {exc}") from exc



"""
PropertyLensService — fetches Australian property data from PropertyLens API.
Falls back to mock data if the API is unavailable.
"""

import logging
import httpx

from app.config import settings
from app.schemas.location import LocationSummary
from app.schemas.report import PropertyListing

from app.schemas.geography import GeographyMetadata
from datetime import date

logger = logging.getLogger(__name__)


MOCK_LISTINGS: list[PropertyListing] = [
    PropertyListing(
        address="1 Example St, Sydney NSW 2000",
        price="$850,000",
        price_numeric=850000,
        beds=3,
        baths=2.0,
        sqft=180,
        listing_type="sold",
        property_type="house",
        source="mock",
        metadata=GeographyMetadata(
            geography_type="mock",
            geography_id="mock",
            source="mock",
            as_of_date=date.today().isoformat()
        )
    ),
    PropertyListing(
        address="2 Sample Ave, Melbourne VIC 3000",
        price="$620,000",
        price_numeric=620000,
        beds=2,
        baths=1.0,
        sqft=95,
        listing_type="active",
        property_type="unit",
        source="mock",
        metadata=GeographyMetadata(
            geography_type="mock",
            geography_id="mock",
            source="mock",
            as_of_date=date.today().isoformat()
        )
    ),
    PropertyListing(
        address="3 Demo Rd, Brisbane QLD 4000",
        price="$540,000",
        price_numeric=540000,
        beds=3,
        baths=2.0,
        sqft=150,
        listing_type="active",
        property_type="townhouse",
        source="mock",
        metadata=GeographyMetadata(
            geography_type="mock",
            geography_id="mock",
            source="mock",
            as_of_date=date.today().isoformat()
        )
    ),
]


class ServiceUnavailableError(Exception):
    """Raised when an external data service is unreachable."""


class PropertyLensService:
    BASE_URL = "https://app.propertylens.au/api/v1"

    def _safe_int(self, value):
        if value is None:
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return int(value)

        if isinstance(value, str):
            digits = "".join(filter(str.isdigit, value))
            if digits:
                return int(digits)

        return None

    def normalize_listing(self, raw: dict, location: LocationSummary) -> PropertyListing:
        """
        Convert PropertyLens property payload into PropertyListing.
        """

        address = (
            raw.get("address")
            or raw.get("full_address")
            or raw.get("display_address")
            or "Unknown"
        )

        price_numeric = (
            raw.get("price")
            or raw.get("estimated_value")
            or raw.get("median_price")
            or raw.get("sale_price")
        )

        price_numeric = self._safe_int(price_numeric)

        price_display = (
            f"${price_numeric:,}"
            if price_numeric
            else "Price unavailable"
        )

        beds = (
            raw.get("bedrooms")
            or raw.get("beds")
            or 0
        )

        baths = (
            raw.get("bathrooms")
            or raw.get("baths")
            or 0
        )

        sqft = (
            raw.get("building_area")
            or raw.get("land_area")
            or raw.get("floor_area")
            or raw.get("sqft")
        )

        property_type = (
            raw.get("property_type")
            or raw.get("propertyType")
            or "house"
        ).lower()

        property_type_map = {
            "apartment": "unit",
            "flat": "unit",
            "studio": "unit",
            "villa": "townhouse",
        }

        property_type = property_type_map.get(
            property_type,
            property_type,
        )

        if property_type not in (
            "house",
            "unit",
            "townhouse",
            "land",
            "other",
        ):
            property_type = "other"

        listing_type = (
            raw.get("listing_type")
            or raw.get("status")
            or "active"
        )

        return PropertyListing(
            address=address,
            price=price_display,
            price_numeric=price_numeric,
            beds=int(beds or 0),
            baths=float(baths or 0),
            sqft=sqft,
            listing_type=str(listing_type).lower(),
            property_type=property_type,
            source="propertylens",
            metadata=GeographyMetadata(
                geography_type="suburb" if location.suburb else "postcode",
                geography_id=location.suburb or location.postcode or location.city,
                source="propertylens",
                as_of_date=date.today().isoformat()
            )
        )

    async def fetch_listings(
        self,
        location: LocationSummary,
    ) -> list[PropertyListing]:
        """
        Search PropertyLens properties using suburb/city/postcode.

        Returns:
            list[PropertyListing]
        """

        api_key = getattr(
            settings,
            "PROPERTYLENS_API_KEY",
            None,
        )

        if not api_key or api_key.startswith("<"):
            logger.warning(
                "PropertyLens API key not configured; no comparable listings"
            )
            return []

        search_query = (
            location.suburb
            or location.city
            or location.postcode
        )

        if not search_query:
            logger.warning(
                "No search query available; no comparable listings"
            )
            return []

        headers = {
            "X-API-Key": api_key,
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/properties/search",
                    params={"q": search_query},
                    headers=headers,
                )

                response.raise_for_status()

                data = response.json()

                if isinstance(data, list):
                    properties = data

                elif isinstance(data, dict):
                    properties = (
                        data.get("properties")
                        or data.get("results")
                        or data.get("data")
                        or []
                    )

                else:
                    properties = []

                listings = [
                    self.normalize_listing(item, location)
                    for item in properties[:20]
                ]

                if not listings:
                    logger.warning(
                        "PropertyLens returned no properties for '%s'",
                        search_query,
                    )
                    return []

                return listings

            except httpx.HTTPStatusError as exc:
                # PropertyLens free tier is very limited (≈5 requests/day, 2/min).
                # On 429 (rate limit) or 403 (daily limit), degrade gracefully to an
                # empty list — the report still renders, comparables show an empty
                # state rather than fake placeholder rows. Redis caching keeps calls rare.
                if exc.response.status_code in (403, 429):
                    logger.warning(
                        "PropertyLens limit hit (HTTP %s) for '%s'; no comparable listings",
                        exc.response.status_code,
                        search_query,
                    )
                    return []
                logger.error(
                    "PropertyLens HTTP error %s: %s",
                    exc.response.status_code,
                    exc.response.text,
                )
                raise ServiceUnavailableError(
                    f"PropertyLens HTTP error: {exc}"
                ) from exc

            except httpx.RequestError as exc:
                logger.error(
                    "PropertyLens request error: %s",
                    exc,
                )
                raise ServiceUnavailableError(
                    f"PropertyLens request failed: {exc}"
                ) from exc

            except Exception as exc:
                logger.exception(
                    "Unexpected PropertyLens error"
                )
                raise ServiceUnavailableError(
                    f"PropertyLens unavailable: {exc}"
                ) from exc