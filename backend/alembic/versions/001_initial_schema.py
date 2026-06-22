"""Initial schema — create all tables.

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("image", sa.String(512), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False, server_default="credentials"),
        sa.Column("tier", sa.String(20), nullable=False, server_default="regular"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ------------------------------------------------------------------
    # locations
    # ------------------------------------------------------------------
    op.create_table(
        "locations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("display_name", sa.String(512), nullable=False),
        sa.Column("suburb", sa.String(255), nullable=True),
        sa.Column("city", sa.String(255), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("postcode", sa.String(10), nullable=True),
        sa.Column("country", sa.String(100), nullable=False, server_default="Australia"),
        sa.Column("country_code", sa.String(3), nullable=False, server_default="AU"),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("nominatim_place_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    # ------------------------------------------------------------------
    # reports
    # ------------------------------------------------------------------
    op.create_table(
        "reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("share_token", sa.String(8), nullable=False),
        sa.Column("market_overview", sa.Text(), nullable=True),
        sa.Column("neighbourhood_insights", sa.Text(), nullable=True),
        sa.Column("demographics_section", sa.Text(), nullable=True),
        sa.Column("investment_intelligence", sa.Text(), nullable=True),
        sa.Column("comparable_properties", sa.Text(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("median_price", sa.String(50), nullable=True),
        sa.Column("price_appreciation", sa.String(50), nullable=True),
        sa.Column("rental_yield", sa.String(50), nullable=True),
        sa.Column("days_on_market", sa.Integer(), nullable=True),
        sa.Column("roi_estimate", sa.String(50), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("share_token", name="uq_reports_share_token"),
    )
    op.create_index("ix_reports_user_id", "reports", ["user_id"])
    op.create_index("ix_reports_location_id", "reports", ["location_id"])

    # ------------------------------------------------------------------
    # saved_locations
    # ------------------------------------------------------------------
    op.create_table(
        "saved_locations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "user_id", "location_id", name="uq_saved_location_user_location"
        ),
    )
    op.create_index("ix_saved_locations_user_id", "saved_locations", ["user_id"])
    op.create_index("ix_saved_locations_location_id", "saved_locations", ["location_id"])

    # ------------------------------------------------------------------
    # watchlist_entries
    # ------------------------------------------------------------------
    op.create_table(
        "watchlist_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "user_id", "location_id", name="uq_watchlist_user_location"
        ),
    )
    op.create_index("ix_watchlist_entries_user_id", "watchlist_entries", ["user_id"])
    op.create_index("ix_watchlist_entries_location_id", "watchlist_entries", ["location_id"])

    # ------------------------------------------------------------------
    # aggregated_market_data
    # ------------------------------------------------------------------
    op.create_table(
        "aggregated_market_data",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("data_source", sa.String(50), nullable=False),
        sa.Column("data_type", sa.String(50), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("is_stale", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_aggregated_market_data_location_id", "aggregated_market_data", ["location_id"]
    )


def downgrade() -> None:
    op.drop_table("aggregated_market_data")
    op.drop_table("watchlist_entries")
    op.drop_table("saved_locations")
    op.drop_table("reports")
    op.drop_table("locations")
    op.drop_table("users")
