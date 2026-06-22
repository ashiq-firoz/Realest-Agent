"""
GeminiService — constructs prompts, calls Gemini 1.5 Pro, parses 6-section responses.

Implements a single correction retry when sections are missing.
Falls back to a partial report with AI Summary placeholder on any error.
"""
from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

import google.generativeai as genai

from app.config import settings

if TYPE_CHECKING:
    from app.schemas.location import LocationSummary
    from app.schemas.report import AggregatedDataBundle

logger = logging.getLogger(__name__)

REQUIRED_SECTIONS = [
    "Market Overview",
    "Neighbourhood Insights",
    "Demographics",
    "Investment Intelligence",
    "Comparable Properties",
    "AI Summary",
]

AI_SUMMARY_PLACEHOLDER = (
    "AI Summary temporarily unavailable. Please retry."
)


class GeminiError(Exception):
    """Raised when the Gemini API returns an unrecoverable error."""


class GeminiService:
    def __init__(self) -> None:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel("gemini-2.5-flash-lite")

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def build_prompt(self, location: "LocationSummary", data: "AggregatedDataBundle") -> str:
        """
        Build the structured prompt injecting location context and JSON data block.
        Instructs the model to produce all 6 sections with ## headers.
        """
        data_block = json.dumps(
            {
                "market_metrics": data.market_metrics.model_dump(),
                "demographics": data.demographics.model_dump(),
                "neighbourhood_amenities": data.amenities.model_dump() if data.amenities else None,
                "listings": [l.model_dump() for l in data.listings[:10]],
            },
            indent=2,
            default=str,
        )

        section_list = "\n".join(f"## {s}" for s in REQUIRED_SECTIONS)

        prompt = f"""You are a professional real estate analyst. Generate a comprehensive real estate intelligence report for:

Location: {location.display_name}
City: {location.city}, {location.state}

Use the following Australian property market data as your primary source. Reference specific data points in your analysis.

```json
{data_block}
```

DATA PROVENANCE — read the "source" of each value before using it:
- "abs_census_2021", "abs", "abs_rppi", "openstreetmap"/"osm", "propertylens" = REAL data; cite these confidently.
- "estimate" = an approximation where no free live source exists (median sale price, rental yield, days on market); present these as *estimates* (e.g. "estimated at ~$X"), never as confirmed figures.
- "mock"/"unavailable" = data could not be retrieved; acknowledge the gap rather than inventing numbers.
- The comparable listings are real properties but DO NOT include sale prices; describe them by type/beds/baths/location and do not fabricate prices.

Generate a complete report with EXACTLY these 6 sections, each starting with the exact ## header shown:

{section_list}

Requirements:
- Market Overview: Summarise current market conditions, price trends (real ABS appreciation), and supply/demand dynamics
- Neighbourhood Insights: Use the real neighbourhood_amenities counts (schools, hospitals, transport, supermarkets, parks, walkability/lifestyle scores) to describe amenities, infrastructure, and liveability
- Demographics: Analyse the real ABS population, age groups, median age, and median household income
- Investment Intelligence: Evaluate investment potential, rental yield, ROI, and risk factors (flag which figures are estimates)
- Comparable Properties: Summarise the real comparable listings provided (type/beds/baths/suburb), noting prices are not available. If the listings array is empty, clearly state that comparable listing data is not currently available for this location and do NOT invent any properties
- AI Summary: Include sub-sections: **Market Summary**, **Investment Recommendation**, **Risk Indicators**, **Opportunities**

Write in professional markdown. Reference specific numbers from the data provided and be transparent about estimates."""

        return prompt

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def parse_sections(self, response_text: str) -> dict[str, str]:
        """
        Extract each of the 6 sections from the Markdown response.
        Uses regex anchored to ## {SectionName} headers.
        Returns dict mapping section name → content string.
        """
        sections: dict[str, str] = {}

        # Build pattern that matches any of the required section headers
        for section in REQUIRED_SECTIONS:
            # Match ## Section Name (case-insensitive, allowing trailing spaces)
            pattern = rf"##\s+{re.escape(section)}\s*\n(.*?)(?=\n##\s+|\Z)"
            match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section] = match.group(1).strip()

        return sections

    def validate_sections(self, sections: dict[str, str]) -> list[str]:
        """
        Return list of section names that are missing or have empty content.
        Empty list means all 6 sections are present and non-empty.
        """
        return [
            s for s in REQUIRED_SECTIONS
            if s not in sections or not sections[s].strip()
        ]

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    async def generate_report(
        self,
        location: "LocationSummary",
        data: "AggregatedDataBundle",
    ) -> dict[str, str]:
        """
        Call Gemini 1.5 Pro and return a dict of all 6 report sections.

        Steps:
        1. Build prompt and call Gemini
        2. Parse and validate sections
        3. If sections missing: re-prompt once with correction instruction
        4. On any error: return partial report with AI Summary placeholder
        """
        try:
            prompt = self.build_prompt(location, data)
            response = self._model.generate_content(prompt)
            response_text = response.text

            sections = self.parse_sections(response_text)
            missing = self.validate_sections(sections)

            if missing:
                logger.warning("Gemini response missing sections: %s. Retrying.", missing)
                correction_prompt = (
                    f"{prompt}\n\nThe following sections were missing from your previous response: "
                    f"{', '.join(missing)}. Please regenerate the COMPLETE report including ALL 6 sections."
                )
                retry_response = self._model.generate_content(correction_prompt)
                sections = self.parse_sections(retry_response.text)

        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            # Return partial report with placeholder for AI Summary
            return {
                "Market Overview": _placeholder("Market Overview"),
                "Neighbourhood Insights": _placeholder("Neighbourhood Insights"),
                "Demographics": _placeholder("Demographics"),
                "Investment Intelligence": _placeholder("Investment Intelligence"),
                "Comparable Properties": _placeholder("Comparable Properties"),
                "AI Summary": AI_SUMMARY_PLACEHOLDER,
            }

        # Ensure all sections have at least a placeholder value
        for section in REQUIRED_SECTIONS:
            if section not in sections or not sections[section].strip():
                sections[section] = (
                    AI_SUMMARY_PLACEHOLDER
                    if section == "AI Summary"
                    else _placeholder(section)
                )

        return sections


    async def generate_investment_insights(self, analytics_data: list[dict]) -> str:
        """
        Call Gemini to generate a short insight comparing top investment opportunities.
        """
        if not analytics_data:
            return "Save more locations and generate reports to unlock AI-powered investment insights."

        data_block = json.dumps(analytics_data, indent=2, default=str)
        prompt = f"""You are a professional real estate investment analyst.
You have been provided with the following data representing a user's saved locations and their key metrics:

```json
{data_block}
```

Write a brief (1-2 paragraphs) insight summarizing the best investment opportunities among these locations.
Focus on comparing the ROI Estimates and Rental Yields. Mention specific locations and numbers.
If there is not enough data or only one location, just briefly comment on it.
Do not use markdown headers, just plain paragraphs.
"""
        try:
            response = self._model.generate_content(prompt)
            return response.text.strip()
        except Exception as exc:
            logger.error("Gemini API error during investment insights: %s", exc)
            return "Investment insights are temporarily unavailable."

def _placeholder(section_name: str) -> str:
    return f"*{section_name} data is temporarily unavailable. Please retry.*"
