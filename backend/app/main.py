"""
FastAPI application entry point.

Registers all routers, CORS middleware, and global exception handlers.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings, settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exception types (raised by services, caught here)
# ---------------------------------------------------------------------------

class LocationNotFoundError(Exception):
    """Raised when a requested location does not exist in the database."""


class ReportGenerationError(Exception):
    """Raised when report generation fails (e.g., Gemini timeout)."""


class ServiceUnavailableError(Exception):
    """Raised when an external data service (Domain, ABS, GovData) is unreachable."""


class CacheError(Exception):
    """Raised for non-recoverable Redis errors that should surface to the caller."""


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    logger.info("Starting Cotality Intelligence API")
    # Instantiate Settings to ensure env vars are validated immediately
    get_settings()
    yield
    logger.info("Shutting down Cotality Intelligence API")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Cotality Intelligence API",
    description="Real estate intelligence platform for the Australian property market.",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(LocationNotFoundError)
async def location_not_found_handler(request: Request, exc: LocationNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc) or "Location not found."},
    )


@app.exception_handler(ReportGenerationError)
async def report_generation_error_handler(request: Request, exc: ReportGenerationError):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "Report generation failed."},
    )


@app.exception_handler(ServiceUnavailableError)
async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError):
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc) or "An external service is currently unavailable."},
    )


@app.exception_handler(CacheError)
async def cache_error_handler(request: Request, exc: CacheError):
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc) or "Cache service error."},
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------
# Routers are imported here to avoid circular imports at module load time.
# Each router file may not exist yet during scaffold; imports are deferred
# inside a try/except so the app still starts during development.

def _register_routers() -> None:
    from app.routers import auth, locations, reports, dashboard, watchlist, agent  # noqa: PLC0415

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(locations.router, prefix="/locations", tags=["locations"])
    app.include_router(reports.router, prefix="/reports", tags=["reports"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
    app.include_router(agent.router, prefix="/agent", tags=["agent"])


try:
    _register_routers()
except ImportError as exc:  # pragma: no cover
    logger.warning("One or more routers could not be imported yet: %s", exc)
