"""
GovDataService — market metrics for a location.

Real, free data where it exists:
  * price_appreciation_yoy  — ABS Residential Property Price Index (RPPI), the
    "% change from corresponding quarter of previous year", by capital city.
  * median_rent_weekly      — real ABS Census G02 value, injected by the aggregation
    layer (from the demographics fetch) when available.

No free API publishes live suburb-level median sale price / yield / days-on-market,
so those are estimated from per-state baselines and tagged source="estimate". The
estimates seed the Gemini prompt, which is instructed to treat them as estimates.
"""
import logging
from datetime import date

import httpx

from app.config import settings
from app.schemas.geography import GeographyMetadata
from app.schemas.location import LocationSummary
from app.schemas.report import MarketMetrics, MetricValue

logger = logging.getLogger(__name__)

_TODAY = date.today().isoformat()

MOCK_MARKET_METRICS = MarketMetrics(
    median_sale_price=MetricValue(value=750000, source="govdata_mock", date=_TODAY),
    median_rent_weekly=MetricValue(value=480, source="govdata_mock", date=_TODAY),
    price_appreciation_yoy=MetricValue(value=4.5, source="govdata_mock", date=_TODAY),
    rental_yield=MetricValue(value=3.3, source="govdata_mock", date=_TODAY),
    days_on_market=MetricValue(value=28, source="govdata_mock", date=_TODAY),
    clearance_rate=MetricValue(value=72.0, source="govdata_mock", date=_TODAY),
    inventory_level=MetricValue(value="medium", source="govdata_mock", date=_TODAY),
    market_sentiment=MetricValue(value="balanced", source="govdata_mock", date=_TODAY),
    metadata=GeographyMetadata(
        geography_type="mock", geography_id="mock", source="govdata_mock", as_of_date=_TODAY
    ),
)

# State -> ABS RPPI capital-city region code.
_RPPI_REGION = {
    "NSW": "1GSYD", "VIC": "2GMEL", "QLD": "3GBRI", "SA": "4GADE",
    "WA": "5GPER", "TAS": "6GHOB", "NT": "7GDAR", "ACT": "8ACTE",
}

# Rough per-state capital-city baselines used ONLY to seed the estimated metrics.
_STATE_BASELINE = {
    "NSW": {"price": 1150000, "rent": 700, "dom": 30},
    "VIC": {"price": 780000, "rent": 560, "dom": 32},
    "QLD": {"price": 760000, "rent": 600, "dom": 28},
    "WA":  {"price": 640000, "rent": 620, "dom": 25},
    "SA":  {"price": 720000, "rent": 560, "dom": 27},
    "TAS": {"price": 660000, "rent": 520, "dom": 34},
    "ACT": {"price": 860000, "rent": 650, "dom": 30},
    "NT":  {"price": 580000, "rent": 620, "dom": 38},
}
_DEFAULT_BASELINE = {"price": 750000, "rent": 550, "dom": 30}


class ServiceUnavailableError(Exception):
    """Raised when an external data service is unreachable."""


class GovDataService:
    RPPI_BASE = getattr(settings, "ABS_API_BASE", "https://data.api.abs.gov.au")

    async def _fetch_appreciation_yoy(self, state: str) -> tuple[float, str] | None:
        """Latest ABS RPPI year-on-year % change for the state's capital city.

        Returns (value, period) e.g. (5.4, "2024-Q2"), or None if unavailable.
        """
        region = _RPPI_REGION.get((state or "").upper())
        if not region:
            return None
        # MEASURE=3 (YoY % change) . PROPERTY_TYPE=3 (Residential property) . REGION . FREQ=Q
        datakey = f"3.3.{region}.Q"
        url = f"{self.RPPI_BASE}/rest/data/RPPI/{datakey}"
        params = {"dimensionAtObservation": "AllDimensions", "format": "jsondata"}
        headers = {"Accept": "application/vnd.sdmx.data+json"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                payload = resp.json()
        except (httpx.HTTPError, ValueError, Exception) as exc:  # noqa: BLE001
            logger.warning("ABS RPPI error for %s: %s", state, exc)
            return None

        data = payload.get("data", {})
        structures = data.get("structures") or ([data["structure"]] if data.get("structure") else [])
        datasets = data.get("dataSets", [])
        if not structures or not datasets:
            return None

        obs_dims = structures[0]["dimensions"]["observation"]
        time_pos = next((i for i, d in enumerate(obs_dims) if d.get("id") == "TIME_PERIOD"), None)
        time_vals = obs_dims[time_pos]["values"] if time_pos is not None else []
        observations = datasets[0].get("observations", {})

        # Pick the observation with the latest time-period index.
        best_idx, best_value = -1, None
        for key, value in observations.items():
            try:
                t_idx = int(key.split(":")[time_pos])
            except (ValueError, IndexError, TypeError):
                continue
            if value and value[0] is not None and t_idx > best_idx:
                best_idx, best_value = t_idx, value[0]
        if best_value is None or best_idx < 0:
            return None
        try:
            period = time_vals[best_idx]["id"]
        except (IndexError, KeyError):
            period = ""
        return round(float(best_value), 1), period

    @staticmethod
    def _appreciation_metric(appr: tuple[float, str] | None) -> MetricValue:
        """Use the real RPPI value only when it is reasonably current (the ABS RPPI
        series can be stale); otherwise fall back to a clearly-labelled estimate so
        a years-old boom figure is never shown as today's appreciation."""
        if appr is not None:
            value, period = appr
            year = None
            if period and period[:4].isdigit():
                year = int(period[:4])
            if year and year >= date.today().year - 2:
                return MetricValue(value=value, source="abs_rppi", date=period)
        return MetricValue(value=4.0, source="estimate", date=_TODAY)

    async def fetch_market_data(self, location: LocationSummary) -> MarketMetrics:
        """
        Build MarketMetrics: real RPPI appreciation where available + per-state
        estimates for the metrics no free API exposes. Never raises — returns
        estimate-tagged values (the aggregation layer overlays real ABS rent later).
        """
        state = (location.state or "").upper()
        baseline = _STATE_BASELINE.get(state, _DEFAULT_BASELINE)

        appreciation_metric = self._appreciation_metric(
            await self._fetch_appreciation_yoy(state)
        )

        est_price = baseline["price"]
        est_rent = baseline["rent"]
        est_yield = round((est_rent * 52) / est_price * 100, 1) if est_price else 3.5

        geo_id = location.suburb or location.postcode or location.city
        return MarketMetrics(
            median_sale_price=MetricValue(value=est_price, source="estimate", date=_TODAY),
            median_rent_weekly=MetricValue(value=est_rent, source="estimate", date=_TODAY),
            price_appreciation_yoy=appreciation_metric,
            rental_yield=MetricValue(value=est_yield, source="estimate", date=_TODAY),
            days_on_market=MetricValue(value=baseline["dom"], source="estimate", date=_TODAY),
            clearance_rate=None,
            inventory_level=MetricValue(value="medium", source="estimate", date=_TODAY),
            market_sentiment=MetricValue(value="balanced", source="estimate", date=_TODAY),
            metadata=GeographyMetadata(
                geography_type="suburb" if location.suburb else "postcode",
                geography_id=geo_id,
                source="abs_rppi+estimate",
                as_of_date=_TODAY,
            ),
        )
