"""
Tests for app.worker.retry_scheduler.

Uses fakeredis to avoid needing a real Redis server.
"""

import pytest
import fakeredis.aioredis
from unittest.mock import patch, AsyncMock

from app.worker.retry_scheduler import (
    BACKOFF_SCHEDULE,
    DEFAULT_BACKOFF_MINUTES,
    RETRY_BACKOFF_KEY_PREFIX,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patch_redis(fake_redis_instance):
    """
    Patch redis.from_url inside retry_scheduler to return a fakeredis instance.
    The module calls `redis.from_url(...)` directly, so we patch at that level.
    """
    def _from_url(url, **kwargs):
        return fake_redis_instance

    return patch("app.worker.retry_scheduler.redis.from_url", side_effect=_from_url)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_backoff_schedule_progression():
    """Verify attempt 1→15min, 2→60min, 3→360min, 4+→1440min."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with _patch_redis(fake):
        from app.worker.retry_scheduler import get_backoff_minutes, increment_backoff_attempt

        # No attempts yet → next is attempt 1 → 15 minutes
        minutes_1 = await get_backoff_minutes("key-abc")
        assert minutes_1 == BACKOFF_SCHEDULE[1]  # 15

        await increment_backoff_attempt("key-abc")
        # Now stored as 1 → get_backoff_minutes adds 1 → attempt 2 → 60 min
        minutes_2 = await get_backoff_minutes("key-abc")
        assert minutes_2 == BACKOFF_SCHEDULE[2]  # 60

        await increment_backoff_attempt("key-abc")
        # Stored as 2 → attempt 3 → 360 min
        minutes_3 = await get_backoff_minutes("key-abc")
        assert minutes_3 == BACKOFF_SCHEDULE[3]  # 360

        await increment_backoff_attempt("key-abc")
        # Stored as 3 → attempt 4 → not in schedule → DEFAULT_BACKOFF_MINUTES
        minutes_4 = await get_backoff_minutes("key-abc")
        assert minutes_4 == DEFAULT_BACKOFF_MINUTES  # 1440

    await fake.aclose()


@pytest.mark.asyncio
async def test_clear_backoff_resets():
    """After clear_backoff, the next get_backoff_minutes returns attempt 1 delay."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with _patch_redis(fake):
        from app.worker.retry_scheduler import (
            get_backoff_minutes,
            increment_backoff_attempt,
            clear_backoff,
        )

        # Advance to attempt 3
        await increment_backoff_attempt("key-xyz")
        await increment_backoff_attempt("key-xyz")
        await increment_backoff_attempt("key-xyz")

        minutes_before = await get_backoff_minutes("key-xyz")
        assert minutes_before == DEFAULT_BACKOFF_MINUTES  # attempt 4 → 1440

        # Clear and verify reset
        await clear_backoff("key-xyz")
        minutes_after = await get_backoff_minutes("key-xyz")
        assert minutes_after == BACKOFF_SCHEDULE[1]  # back to attempt 1 → 15

    await fake.aclose()


@pytest.mark.asyncio
async def test_increment_persists_attempt_count():
    """increment_backoff_attempt correctly stores the incremented count."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with _patch_redis(fake):
        from app.worker.retry_scheduler import increment_backoff_attempt

        await increment_backoff_attempt("persist-key")
        value = await fake.get(f"{RETRY_BACKOFF_KEY_PREFIX}persist-key")
        assert value == "1"

        await increment_backoff_attempt("persist-key")
        value = await fake.get(f"{RETRY_BACKOFF_KEY_PREFIX}persist-key")
        assert value == "2"

    await fake.aclose()


@pytest.mark.asyncio
async def test_backoff_ttl_set():
    """increment_backoff_attempt sets a TTL of 7 days on the key."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with _patch_redis(fake):
        from app.worker.retry_scheduler import increment_backoff_attempt

        await increment_backoff_attempt("ttl-key")

    expected_max_ttl_seconds = 7 * 24 * 3600
    ttl = await fake.ttl(f"{RETRY_BACKOFF_KEY_PREFIX}ttl-key")
    # TTL should be set and within 7 days
    assert 0 < ttl <= expected_max_ttl_seconds
    await fake.aclose()


@pytest.mark.asyncio
async def test_clear_backoff_removes_key():
    """clear_backoff deletes the Redis key entirely."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with _patch_redis(fake):
        from app.worker.retry_scheduler import increment_backoff_attempt, clear_backoff

        await increment_backoff_attempt("delete-me")
        key = f"{RETRY_BACKOFF_KEY_PREFIX}delete-me"
        assert await fake.exists(key) == 1

        await clear_backoff("delete-me")
        assert await fake.exists(key) == 0

    await fake.aclose()


@pytest.mark.asyncio
async def test_check_and_resume_paused_executions():
    """Paused executions with an active API key are re-enqueued."""
    import uuid
    from app.models.enums import TaskExecutionStatus, APIKeyStatus
    from contextlib import asynccontextmanager
    from unittest.mock import MagicMock

    exec_id = uuid.uuid4()
    key_id = uuid.uuid4()

    execution = MagicMock()
    execution.id = exec_id
    execution.api_key_id = key_id
    execution.current_step_index = 0
    execution.status = TaskExecutionStatus.paused_exhausted

    api_key = MagicMock()
    api_key.status = APIKeyStatus.active

    async def _db_get(model_class, pk):
        from app.models import TaskExecution, APIKey
        if model_class is APIKey:
            return api_key
        return None

    session = AsyncMock()
    session.execute = AsyncMock()
    session.get = _db_get
    session.commit = AsyncMock()

    # Mock scalars().all() to return our execution
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [execution]
    session.execute.return_value = mock_result

    @asynccontextmanager
    async def _factory():
        yield session

    enqueue_mock = AsyncMock()

    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with (
        patch("app.worker.retry_scheduler.redis.from_url", return_value=fake),
        patch("app.worker.retry_scheduler.async_session_factory", side_effect=_factory),
        patch("app.worker.retry_scheduler.enqueue_job", new=enqueue_mock),
    ):
        from app.worker.retry_scheduler import check_and_resume_paused_executions
        await check_and_resume_paused_executions()

    enqueue_mock.assert_awaited_once()
    enqueued = enqueue_mock.call_args[0][0]
    assert enqueued.task_execution_id == exec_id
    assert enqueued.step_index == 0
    assert enqueued.api_key_id == key_id

    await fake.aclose()
