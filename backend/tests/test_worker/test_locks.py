"""
Tests for app.worker.locks using fakeredis.

fakeredis provides an in-process Redis emulator with the same interface
as redis.asyncio, so no real Redis server is needed.
"""

import pytest
import fakeredis.aioredis
from unittest.mock import patch, AsyncMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patch_redis(fake_redis_instance):
    """
    Patch app.worker.locks.get_redis to return a pre-created fakeredis instance.
    We wrap it in an async function since get_redis is async.
    """
    async def _get_fake():
        return fake_redis_instance

    return patch("app.worker.locks.get_redis", new=_get_fake)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_acquire_lock_success():
    """First acquire on a fresh key succeeds and returns True."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with _patch_redis(fake):
        from app.worker.locks import acquire_lock
        result = await acquire_lock("test-api-key-1")

    assert result is True
    await fake.aclose()


@pytest.mark.asyncio
async def test_acquire_lock_contention():
    """Second acquire while first lock is held returns False."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with _patch_redis(fake):
        from app.worker.locks import acquire_lock
        first = await acquire_lock("test-api-key-2", ttl_ms=30_000)
        second = await acquire_lock("test-api-key-2", ttl_ms=30_000)

    assert first is True
    assert second is False
    await fake.aclose()


@pytest.mark.asyncio
async def test_release_lock():
    """After release_lock, another acquire on the same key succeeds."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with _patch_redis(fake):
        from app.worker.locks import acquire_lock, release_lock
        first = await acquire_lock("test-api-key-3")
        assert first is True

        await release_lock("test-api-key-3")

        second = await acquire_lock("test-api-key-3")
        assert second is True

    await fake.aclose()


@pytest.mark.asyncio
async def test_release_lock_safe_when_not_held():
    """release_lock is safe to call even when the lock was never acquired."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with _patch_redis(fake):
        from app.worker.locks import release_lock
        # Should not raise
        await release_lock("nonexistent-key")

    await fake.aclose()


@pytest.mark.asyncio
async def test_lock_key_prefix():
    """Verify the lock is stored with the correct Redis key prefix."""
    from app.worker.locks import LOCK_PREFIX
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with _patch_redis(fake):
        from app.worker.locks import acquire_lock
        await acquire_lock("my-key-id")

    expected_key = f"{LOCK_PREFIX}my-key-id"
    value = await fake.get(expected_key)
    assert value == "1"
    await fake.aclose()


@pytest.mark.asyncio
async def test_lock_ttl_set():
    """Verify the lock has a TTL (will expire)."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with _patch_redis(fake):
        from app.worker.locks import acquire_lock, LOCK_PREFIX
        await acquire_lock("ttl-test-key", ttl_ms=5_000)

    ttl_ms = await fake.pttl(f"{LOCK_PREFIX}ttl-test-key")
    # TTL should be set (positive value) and at most 5000ms
    assert 0 < ttl_ms <= 5_000
    await fake.aclose()


@pytest.mark.asyncio
async def test_wait_for_lock_acquires_when_free():
    """wait_for_lock succeeds immediately when the lock is not held."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with _patch_redis(fake):
        from app.worker.locks import wait_for_lock
        result = await wait_for_lock("free-key", max_wait_seconds=2.0, poll_interval=0.1)

    assert result is True
    await fake.aclose()


@pytest.mark.asyncio
async def test_wait_for_lock_fails_when_contended():
    """wait_for_lock returns False when lock cannot be acquired within timeout."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with _patch_redis(fake):
        from app.worker.locks import acquire_lock, wait_for_lock
        # Hold the lock first
        await acquire_lock("held-key", ttl_ms=60_000)
        # Try to acquire with very short timeout
        result = await wait_for_lock("held-key", max_wait_seconds=0.1, poll_interval=0.05)

    assert result is False
    await fake.aclose()
