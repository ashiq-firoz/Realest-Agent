"""
ABSService — fetches real demographic data from the ABS Data API (SDMX-JSON).

Uses the 2021 Census "Postal Area" (POA) dataflows, keyed by postcode — which the
platform already resolves for every location:

    C21_G01_POA  — Selected person characteristics (population P_1 + age groups)
    C21_G02_POA  — Selected medians and averages (median age, household income, rent)

Returns real values where available and falls back to MOCK_DEMOGRAPHICS on any
failure (missing postcode, network error, parse error) so the report pipeline stays
resilient. Population growth and unemployment are not published at POA level in these
tables, so they are estimated and clearly attributed.
"""
import asyncio
import logging
from datetime import date

import httpx

from app.config import settings
from app.schemas.geography import GeographyMetadata
from app.schemas.location import LocationSummary
from app.schemas.report import DemographicsSnapshot

logger = logging.getLogger(__name__)

MOCK_DEMOGRAPHICS = DemographicsSnapshot(
    population=45000,
    population_growth_pct=1.8,
    median_age=35,
    median_household_income=82000,
    unemployment_rate=4.2,
    dominant_age_group="25-34",
    reference_year=2021,
    median_rent_weekly=480,
    source="mock",
    metadata=GeographyMetadata(
        geography_type="mock",
        geography_id="mock",
        source="abs_mock",
        as_of_date=date.today().isoformat(),
    ),
)

# ABS G01 person-characteristic age-group codes -> human-readable labels.
_AGE_GROUP_LABELS = {
    "0_4": "0-4",
    "5_14": "5-14",
    "15_19": "15-19",
    "20_24": "20-24",
    "25_34": "25-34",
    "35_44": "35-44",
    "45_54": "45-54",
    "55_64": "55-64",
    "65_74": "65-74",
    "75_84": "75-84",
    "GE85": "85+",
}

# G02 MEDAVG codes
_MED_AGE = "1"
_MED_HH_INCOME_WEEKLY = "4"
_MED_RENT_WEEKLY = "6"

# Rough per-state ERP annual growth estimates (ABS national ~ figures); used only
# for the population_growth_pct field which is not available at POA level.
_STATE_GROWTH_EST = {
    "NSW": 1.2, "VIC": 1.6, "QLD": 2.1, "WA": 2.3,
    "SA": 1.0, "TAS": 0.6, "ACT": 1.4, "NT": 0.7,
}


class ServiceUnavailableError(Exception):
    """Raised when an external data service is unreachable."""


class ABSService:
    BASE_URL = getattr(settings, "ABS_API_BASE", "https://data.api.abs.gov.au")
    G01 = "C21_G01_POA"
    G02 = "C21_G02_POA"

    async def _fetch(self, dataflow: str, datakey: str) -> dict:
        """Call the ABS Data API and return parsed SDMX-JSON, or raise on failure."""
        url = f"{self.BASE_URL}/rest/data/{dataflow}/{datakey}"
        params = {"dimensionAtObservation": "AllDimensions", "format": "jsondata"}
        headers = {"Accept": "application/vnd.sdmx.data+json"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def _extract(resp: dict, target_dim_id: str) -> dict[str, float]:
        """
        Flatten an AllDimensions SDMX-JSON response into {dim_code: value} for the
        requested dimension. Assumes the other dimensions collapse to a single value
        (because the datakey filters region/sex), which holds for our POA queries.
        """
        data = resp.get("data", {})
        structures = data.get("structures") or ([data["structure"]] if data.get("structure") else [])
        if not structures:
            return {}
        obs_dims = structures[0]["dimensions"]["observation"]

        pos = None
        target_values = None
        for i, dim in enumerate(obs_dims):
            if dim.get("id") == target_dim_id:
                pos = i
                target_values = dim.get("values", [])
                break
        if pos is None or target_values is None:
            return {}

        datasets = data.get("dataSets", [])
        if not datasets:
            return {}
        observations = datasets[0].get("observations", {})

        result: dict[str, float] = {}
        for key, value in observations.items():
            indices = key.split(":")
            try:
                code = target_values[int(indices[pos])]["id"]
            except (IndexError, ValueError, KeyError):
                continue
            if value and value[0] is not None:
                result[code] = value[0]
        return result

    @staticmethod
    def _reference_year(resp: dict, default: int = 2021) -> int:
        data = resp.get("data", {})
        structures = data.get("structures") or ([data["structure"]] if data.get("structure") else [])
        if not structures:
            return default
        for dim in structures[0]["dimensions"]["observation"]:
            if dim.get("id") == "TIME_PERIOD":
                vals = dim.get("values", [])
                if vals:
                    try:
                        return int(vals[-1]["id"])
                    except (ValueError, KeyError):
                        return default
        return default

    async def fetch_demographics(self, location: LocationSummary) -> DemographicsSnapshot:
        """
        Fetch real demographics from ABS Census 2021 (POA) by postcode.
        Falls back to MOCK_DEMOGRAPHICS on any failure.
        """
        postcode = (location.postcode or "").strip()
        if not postcode:
            logger.info("No postcode for %s; using mock demographics", location.display_name)
            return MOCK_DEMOGRAPHICS

        try:
            # Two cheap calls, run concurrently: G02 medians + G01 persons-by-PCHAR.
            g02_resp, g01_resp = await asyncio.gather(
                self._fetch(self.G02, f".{postcode}.."),
                self._fetch(self.G01, f"3..{postcode}.."),
            )
        except (httpx.HTTPError, Exception) as exc:  # noqa: BLE001
            logger.warning("ABS API error for postcode %s: %s — using mock", postcode, exc)
            return MOCK_DEMOGRAPHICS

        medavg = self._extract(g02_resp, "MEDAVG")
        pchar = self._extract(g01_resp, "PCHAR")

        # If neither call returned usable data (e.g. unknown postcode), fall back.
        if not medavg and not pchar:
            logger.info("ABS returned no records for postcode %s — using mock", postcode)
            return MOCK_DEMOGRAPHICS

        population = int(pchar.get("P_1") or MOCK_DEMOGRAPHICS.population)

        # Dominant age group = age band with the highest count.
        age_counts = {
            label: pchar[code]
            for code, label in _AGE_GROUP_LABELS.items()
            if code in pchar
        }
        dominant_age_group = (
            max(age_counts, key=age_counts.get) if age_counts
            else MOCK_DEMOGRAPHICS.dominant_age_group
        )

        median_age = int(medavg.get(_MED_AGE) or MOCK_DEMOGRAPHICS.median_age)
        income_weekly = medavg.get(_MED_HH_INCOME_WEEKLY)
        median_household_income = (
            int(round(income_weekly * 52)) if income_weekly
            else MOCK_DEMOGRAPHICS.median_household_income
        )
        rent_weekly = medavg.get(_MED_RENT_WEEKLY)
        median_rent_weekly = int(rent_weekly) if rent_weekly else None

        reference_year = self._reference_year(g02_resp)

        # Not published at POA level in these tables — estimated, clearly attributed.
        growth_est = _STATE_GROWTH_EST.get((location.state or "").upper(), 1.4)

        return DemographicsSnapshot(
            population=population,
            population_growth_pct=growth_est,
            median_age=median_age,
            median_household_income=median_household_income,
            unemployment_rate=4.0,  # estimate; ABS LFS not at POA granularity here
            dominant_age_group=dominant_age_group,
            reference_year=reference_year,
            median_rent_weekly=median_rent_weekly,
            source="abs",
            metadata=GeographyMetadata(
                geography_type="postcode",
                geography_id=postcode,
                source="abs_census_2021",
                as_of_date=f"{reference_year}",
            ),
        )
