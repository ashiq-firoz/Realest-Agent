"""
Application settings loaded from environment variables.

Required variables must be set or the app will fail fast with a clear error.
"""
from functools import lru_cache
from typing import Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database ---
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    # Constructed from individual parts; can be overridden directly.
    DATABASE_URL: Optional[str] = None

    # --- Redis ---
    REDIS_URL: str

    # --- External APIs ---
    GEMINI_API_KEY: str
    # Domain dropped (its _search needs paid OAuth); kept optional for back-compat.
    DOMAIN_API_KEY: Optional[str] = None
    # PropertyLens provides free comparable listings; mock fallback if unset.
    PROPERTYLENS_API_KEY: Optional[str] = None
    
    # --- Realty in AU RapidAPI ---
    RAPIDAPI_KEY: str
    REALTY_AU_HOST: str = "realty-in-au.p.rapidapi.com"
    # Keyless free data sources (overridable via env if needed).
    ABS_API_BASE: str = "https://data.api.abs.gov.au"
    OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"

    # --- Auth ---
    NEXTAUTH_SECRET: str

    # --- Frontend origin for CORS ---
    FRONTEND_URL: str = "http://localhost:3000"

    # --- Cache ---
    CACHE_TTL_SECONDS: int = 21600  # 6 hours

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        """Construct the asyncpg DATABASE_URL if not explicitly provided."""
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:"
                f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
                f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self

    @field_validator("REDIS_URL")
    @classmethod
    def redis_url_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("REDIS_URL must not be empty")
        return v

    @field_validator("GEMINI_API_KEY")
    @classmethod
    def gemini_key_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("GEMINI_API_KEY must not be empty")
        return v

    @field_validator("NEXTAUTH_SECRET")
    @classmethod
    def nextauth_secret_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("NEXTAUTH_SECRET must not be empty")
        return v


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings. Fails fast if env vars are missing."""
    return Settings()


# Module-level singleton for convenience imports.
settings = get_settings()
