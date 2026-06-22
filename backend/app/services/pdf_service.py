"""
PDFService — renders the Jinja2 HTML template and converts it to PDF via WeasyPrint.
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader

if TYPE_CHECKING:
    from app.schemas.report import ReportResponse

logger = logging.getLogger(__name__)

# Resolve the templates directory relative to this file:
# backend/app/services/pdf_service.py  →  backend/templates/
_TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__),  # backend/app/services/
    "..",                        # backend/app/
    "..",                        # backend/
    "templates",
)


class PDFService:
    """Generates a branded PDF report from a ReportResponse."""

    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(os.path.abspath(_TEMPLATES_DIR)),
            autoescape=False,
        )

    def generate(self, report: "ReportResponse") -> bytes:
        """
        Render report.html with Jinja2 and convert to PDF via WeasyPrint.

        Returns:
            Raw PDF bytes.
        """
        template = self._env.get_template("report.html")

        # Build comparable properties HTML table
        comparable_properties_html = self._render_comparable_properties(
            report.comparable_properties
        )

        created_at_str = (
            report.created_at.strftime("%d %B %Y")
            if report.created_at
            else "—"
        )

        html_content = template.render(
            location_display_name=report.location.display_name,
            created_at=created_at_str,
            report_id=report.id,
            market_overview=report.market_overview,
            neighbourhood_insights=report.neighbourhood_insights,
            demographics_section=report.demographics_section,
            investment_intelligence=report.investment_intelligence,
            comparable_properties_html=comparable_properties_html,
            ai_summary=report.ai_summary,
            median_price=report.median_price,
            price_appreciation=report.price_appreciation,
            rental_yield=report.rental_yield,
            days_on_market=report.days_on_market,
            roi_estimate=report.roi_estimate,
        )

        import weasyprint  # import lazily to avoid startup cost when not needed
        pdf_bytes: bytes = weasyprint.HTML(string=html_content).write_pdf()
        return pdf_bytes

    @staticmethod
    def _render_comparable_properties(listings: list) -> str:
        """Render the comparable properties list as an HTML table."""
        if not listings:
            return "<p><em>No comparable properties available.</em></p>"

        def sqft_display(p: object) -> str:
            sqft = getattr(p, "sqft", None)
            return f"{sqft:,} m²" if sqft else "—"

        rows = "".join(
            f"<tr style='border-bottom:1px solid #e2e8f0'>"
            f"<td style='padding:6px 8px'>{getattr(p, 'address', '—')}</td>"
            f"<td style='padding:6px 8px'>{getattr(p, 'price', '—')}</td>"
            f"<td style='padding:6px 8px;text-align:center'>{getattr(p, 'beds', '—')}</td>"
            f"<td style='padding:6px 8px;text-align:center'>{getattr(p, 'baths', '—')}</td>"
            f"<td style='padding:6px 8px'>{sqft_display(p)}</td>"
            f"<td style='padding:6px 8px;text-transform:capitalize'>{getattr(p, 'listing_type', '—')}</td>"
            f"<td style='padding:6px 8px;text-transform:capitalize'>{getattr(p, 'property_type', '—')}</td>"
            f"</tr>"
            for p in listings
        )

        return (
            "<table style='width:100%;border-collapse:collapse;font-size:9pt'>"
            "<thead><tr style='background:#1a1a2e;color:#fff'>"
            "<th style='padding:6px 8px;text-align:left'>Address</th>"
            "<th style='padding:6px 8px;text-align:left'>Price</th>"
            "<th style='padding:6px 8px;text-align:center'>Beds</th>"
            "<th style='padding:6px 8px;text-align:center'>Baths</th>"
            "<th style='padding:6px 8px;text-align:left'>Size</th>"
            "<th style='padding:6px 8px;text-align:left'>Type</th>"
            "<th style='padding:6px 8px;text-align:left'>Property</th>"
            "</tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
        )
