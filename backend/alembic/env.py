"""
Alembic environment wired to the async SQLAlchemy engine.

This env.py uses the `run_async_migrations()` pattern required for asyncpg.
The `sqlalchemy.url` in alembic.ini is intentionally blank — the URL is
read from `app.config.settings.DATABASE_URL` at runtime.

All models must be imported here so Alembic's autogenerate can detect
schema changes.
"""
import asyncio
import os
import sys
from logging.config import fileConfig

# Ensure the project root (parent of this alembic/ dir) is on sys.path
# so that `from app.config import ...` resolves inside the Docker container.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.database import Base  # noqa: F401 — imports Base with metadata

# ----- Import all models so autogenerate can find them --------------------
# Add new model imports here as they are created.
from app.models.user import User            # noqa: F401
from app.models.location import Location    # noqa: F401
from app.models.report import Report        # noqa: F401
from app.models.saved_location import SavedLocation  # noqa: F401
from app.models.watchlist import WatchlistEntry      # noqa: F401
from app.models.aggregated_data import AggregatedMarketData  # noqa: F401
# --------------------------------------------------------------------------

# Alembic Config object — gives access to values in alembic.ini
config = context.config

# Configure Python logging from the alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with the one from our Pydantic settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Target metadata for autogenerate support
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migrations (no live DB connection)
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Run migrations without an engine connection.
    Generates SQL scripts that can be applied manually.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (async, with live DB connection)
# ---------------------------------------------------------------------------

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations through a sync connection."""
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,  # Use NullPool for migration runs
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online (connected) migrations."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
