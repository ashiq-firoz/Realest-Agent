"""
CacheService — wraps async Redis with typed get/set operations.

Cache key patterns:
    aggregated:{location_id}   TTL: CACHE_TTL_SECONDS (default 6 h)
    report:{report_id}         TTL: 86400 s (24 h)
"""
import json
import logging
from typing import Optional

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.config import settings
from app.schemas.report import AggregatedDataBundle, ReportResponse

logger = logging.getLogger(__name__)


class CacheError(Exception):
    """Raised for non-recoverable Redis errors that should surface to the caller."""


class CacheService:
    def __init__(self, redis_client: aioredis.Redis | None = None) -> None:
        self._redis: aioredis.Redis = redis_client or aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    # ------------------------------------------------------------------
    # Aggregated data cache  (key: "aggregated:{location_id}")
    # ------------------------------------------------------------------

    async def get_aggregated(self, location_id: str) -> Optional[AggregatedDataBundle]:
        """
        Return cached AggregatedDataBundle or None on miss/error.
        Logs and swallows RedisError (non-fatal).
        """
        key = f"aggregated:{location_id}"
        try:
            raw = await self._redis.get(key)
            if raw is None:
                return None
            data = json.loads(raw)
            return AggregatedDataBundle.model_validate(data)
        except RedisError as exc:
            logger.warning("Redis GET error for key %s: %s", key, exc)
            return None

    async def set_aggregated(self, location_id: str, data: AggregatedDataBundle) -> None:
        """
        Serialize AggregatedDataBundle to JSON and store with TTL.
        Logs and swallows RedisError (non-fatal).
        """
        key = f"aggregated:{location_id}"
        try:
            payload = data.model_dump_json()
            await self._redis.set(key, payload, ex=settings.CACHE_TTL_SECONDS)
        except RedisError as exc:
            logger.warning("Redis SET error for key %s: %s", key, exc)

    async def invalidate(self, location_id: str) -> None:
        """
        Delete the aggregated cache entry for a location.
        Logs and swallows RedisError.
        """
        key = f"aggregated:{location_id}"
        try:
            await self._redis.delete(key)
        except RedisError as exc:
            logger.warning("Redis DEL error for key %s: %s", key, exc)

    # ------------------------------------------------------------------
    # Report cache  (key: "report:{report_id}")
    # ------------------------------------------------------------------

    async def get_report(self, report_id: str) -> Optional[ReportResponse]:
        """
        Return cached ReportResponse or None on miss/error.
        TTL: 24 hours.
        """
        key = f"report:{report_id}"
        try:
            raw = await self._redis.get(key)
            if raw is None:
                return None
            data = json.loads(raw)
            return ReportResponse.model_validate(data)
        except RedisError as exc:
            logger.warning("Redis GET error for key %s: %s", key, exc)
            return None

    async def set_report(self, report_id: str, data: ReportResponse) -> None:
        """
        Serialize ReportResponse to JSON and store for 24 hours.
        Logs and swallows RedisError.
        """
        key = f"report:{report_id}"
        try:
            payload = data.model_dump_json()
            await self._redis.set(key, payload, ex=86400)  # 24 h
        except RedisError as exc:
            logger.warning("Redis SET error for key %s: %s", key, exc)


# ------------------------------------------------------------------
# Module-level singleton
# ------------------------------------------------------------------

_cache_service: CacheService | None = None


def get_cache_service() -> CacheService:
    """Return the module-level CacheService singleton."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
