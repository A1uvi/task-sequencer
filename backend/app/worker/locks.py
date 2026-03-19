import asyncio
import logging

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

LOCK_PREFIX = "api_key_lock:"
DEFAULT_LOCK_TTL_MS = 30_000  # 30 seconds max — prevents deadlock if worker crashes


async def get_redis() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


async def acquire_lock(api_key_id: str, ttl_ms: int = DEFAULT_LOCK_TTL_MS) -> bool:
    """Try to acquire distributed lock for api_key_id.
    Returns True if acquired, False if already held by another worker."""
    r = await get_redis()
    key = f"{LOCK_PREFIX}{api_key_id}"
    result = await r.set(key, "1", nx=True, px=ttl_ms)
    await r.aclose()
    return result is not None


async def release_lock(api_key_id: str) -> None:
    """Release the lock. Safe to call even if lock not held."""
    r = await get_redis()
    key = f"{LOCK_PREFIX}{api_key_id}"
    await r.delete(key)
    await r.aclose()


async def wait_for_lock(
    api_key_id: str,
    max_wait_seconds: float = 10.0,
    poll_interval: float = 0.5,
    ttl_ms: int = DEFAULT_LOCK_TTL_MS,
) -> bool:
    """Poll until lock acquired or timeout. Returns True if acquired."""
    deadline = asyncio.get_event_loop().time() + max_wait_seconds
    while asyncio.get_event_loop().time() < deadline:
        if await acquire_lock(api_key_id, ttl_ms):
            return True
        await asyncio.sleep(poll_interval)
    return False
