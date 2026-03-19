"""
Tests for app.worker.executor.execute_task_step.

All external dependencies are mocked:
- DB session (via async_session_factory)
- ai_providers.execute
- decrypt_api_key
- acquire_lock / release_lock
- notification functions
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call
from contextlib import asynccontextmanager

import pytest

from app.worker.jobs import ExecuteTaskStepJob
from app.models.enums import TaskExecutionStatus, APIKeyStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_execution(
    task_execution_id: uuid.UUID,
    api_key_id: uuid.UUID,
    task_version_id: uuid.UUID,
    user_id: uuid.UUID,
    step_index: int = 0,
    status: TaskExecutionStatus = TaskExecutionStatus.queued,
    ordered_prompt_ids: list | None = None,
):
    """Build a mock TaskExecution object."""
    execution = MagicMock()
    execution.id = task_execution_id
    execution.api_key_id = api_key_id
    execution.task_version_id = task_version_id
    execution.created_by = user_id
    execution.status = status
    execution.current_step_index = step_index
    execution.last_prompt_version_id = None
    execution.step_outputs = {}
    return execution


def _make_task_version(prompt_version_ids: list):
    tv = MagicMock()
    tv.ordered_prompt_version_ids = prompt_version_ids
    tv.default_model = "gpt-4o"
    return tv


def _make_prompt_version(content: str = "Summarise this text"):
    pv = MagicMock()
    pv.content = content
    return pv


def _make_api_key(provider: str = "openai", status: APIKeyStatus = APIKeyStatus.active):
    key = MagicMock()
    key.provider = provider
    key.encrypted_key = "encrypted-placeholder"
    key.status = status
    return key


def _make_provider_response(content: str = "AI response"):
    from ai_providers.base import ProviderResponse
    return ProviderResponse(
        content=content,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        raw_response={"choices": [{"message": {"content": content}}]},
    )


def _make_mock_session(
    execution,
    task_version,
    prompt_version,
    api_key,
):
    """Return an AsyncMock DB session whose .get() dispatches by model type."""
    from app.models import TaskExecution, TaskVersion, PromptVersion, APIKey

    async def _get(model_class, pk):
        if model_class is TaskExecution:
            return execution
        if model_class is TaskVersion:
            return task_version
        if model_class is PromptVersion:
            return prompt_version
        if model_class is APIKey:
            return api_key
        return None

    session = AsyncMock()
    session.get = _get
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@asynccontextmanager
async def _session_ctx(session):
    yield session


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ids():
    return {
        "execution": uuid.uuid4(),
        "api_key": uuid.uuid4(),
        "task_version": uuid.uuid4(),
        "user": uuid.uuid4(),
        "prompt_version": uuid.uuid4(),
    }


@pytest.fixture
def sample_job(ids):
    return ExecuteTaskStepJob(
        task_execution_id=ids["execution"],
        step_index=0,
        api_key_id=ids["api_key"],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_happy_path(ids, sample_job):
    """Full happy path: AI call succeeds, conversation stored, step completed."""
    prompt_vid = ids["prompt_version"]
    execution = _make_execution(
        ids["execution"], ids["api_key"], ids["task_version"], ids["user"]
    )
    task_version = _make_task_version([prompt_vid])  # single step
    prompt_version = _make_prompt_version()
    api_key = _make_api_key()
    session = _make_mock_session(execution, task_version, prompt_version, api_key)

    with (
        patch("app.worker.executor.async_session_factory", side_effect=lambda: _session_ctx(session)),
        patch("app.worker.executor.user_can_use_api_key", new=AsyncMock(return_value=True)),
        patch("app.worker.executor.acquire_lock", new=AsyncMock(return_value=True)),
        patch("app.worker.executor.release_lock", new=AsyncMock()),
        patch("app.worker.executor.decrypt_api_key", return_value="sk-plaintext"),
        patch("app.worker.executor.ai_execute", new=AsyncMock(return_value=_make_provider_response())),
        patch("app.worker.executor.enqueue_job", new=AsyncMock()),
        patch("app.worker.executor.notify_task_completed", new=AsyncMock()) as mock_notify,
    ):
        from app.worker.executor import execute_task_step
        await execute_task_step(sample_job)

    # Execution should be marked completed (only 1 step)
    assert execution.status == TaskExecutionStatus.completed
    # Conversation should have been added to the session
    session.add.assert_called_once()
    # step_outputs should contain step 0
    assert "0" in execution.step_outputs
    assert execution.step_outputs["0"]["content"] == "AI response"
    # Notification should have been called
    mock_notify.assert_awaited_once_with(ids["user"], ids["execution"])


@pytest.mark.asyncio
async def test_execute_multistep_enqueues_next(ids):
    """With multiple steps, completing step 0 enqueues step 1."""
    prompt_vid_0 = uuid.uuid4()
    prompt_vid_1 = uuid.uuid4()
    execution = _make_execution(
        ids["execution"], ids["api_key"], ids["task_version"], ids["user"]
    )
    task_version = _make_task_version([prompt_vid_0, prompt_vid_1])
    prompt_version = _make_prompt_version()
    api_key = _make_api_key()
    session = _make_mock_session(execution, task_version, prompt_version, api_key)

    enqueue_mock = AsyncMock()
    with (
        patch("app.worker.executor.async_session_factory", side_effect=lambda: _session_ctx(session)),
        patch("app.worker.executor.user_can_use_api_key", new=AsyncMock(return_value=True)),
        patch("app.worker.executor.acquire_lock", new=AsyncMock(return_value=True)),
        patch("app.worker.executor.release_lock", new=AsyncMock()),
        patch("app.worker.executor.decrypt_api_key", return_value="sk-plaintext"),
        patch("app.worker.executor.ai_execute", new=AsyncMock(return_value=_make_provider_response())),
        patch("app.worker.executor.enqueue_job", new=enqueue_mock),
        patch("app.worker.executor.notify_task_completed", new=AsyncMock()),
    ):
        from app.worker.executor import execute_task_step
        await execute_task_step(ExecuteTaskStepJob(
            task_execution_id=ids["execution"],
            step_index=0,
            api_key_id=ids["api_key"],
        ))

    # enqueue_job called with step_index=1
    enqueue_mock.assert_awaited_once()
    enqueued_job = enqueue_mock.call_args[0][0]
    assert enqueued_job.step_index == 1


@pytest.mark.asyncio
async def test_execute_quota_exhausted(ids, sample_job):
    """QuotaExhaustedError → key marked exhausted, execution paused."""
    from ai_providers.base import QuotaExhaustedError

    execution = _make_execution(
        ids["execution"], ids["api_key"], ids["task_version"], ids["user"]
    )
    prompt_vid = ids["prompt_version"]
    task_version = _make_task_version([prompt_vid])
    prompt_version = _make_prompt_version()
    api_key = _make_api_key()

    # Second session for error handling path
    execution2 = _make_execution(
        ids["execution"], ids["api_key"], ids["task_version"], ids["user"]
    )
    api_key2 = _make_api_key()

    call_count = 0

    async def _get_primary(model_class, pk):
        from app.models import TaskExecution, TaskVersion, PromptVersion, APIKey
        if model_class is TaskExecution:
            return execution
        if model_class is TaskVersion:
            return task_version
        if model_class is PromptVersion:
            return prompt_version
        if model_class is APIKey:
            return api_key
        return None

    async def _get_secondary(model_class, pk):
        from app.models import TaskExecution, TaskVersion, PromptVersion, APIKey
        if model_class is TaskExecution:
            return execution2
        if model_class is APIKey:
            return api_key2
        return None

    session1 = AsyncMock()
    session1.get = _get_primary
    session1.add = MagicMock()
    session1.commit = AsyncMock()

    session2 = AsyncMock()
    session2.get = _get_secondary
    session2.add = MagicMock()
    session2.commit = AsyncMock()

    sessions = [session1, session2]
    idx = 0

    @asynccontextmanager
    async def _factory():
        nonlocal idx
        current = sessions[idx]
        idx += 1
        yield current

    notify_exhausted = AsyncMock()

    with (
        patch("app.worker.executor.async_session_factory", side_effect=_factory),
        patch("app.worker.executor.user_can_use_api_key", new=AsyncMock(return_value=True)),
        patch("app.worker.executor.acquire_lock", new=AsyncMock(return_value=True)),
        patch("app.worker.executor.release_lock", new=AsyncMock()),
        patch("app.worker.executor.decrypt_api_key", return_value="sk-plaintext"),
        patch("app.worker.executor.ai_execute", new=AsyncMock(side_effect=QuotaExhaustedError("quota"))),
        patch("app.worker.executor.notify_token_exhausted", new=notify_exhausted),
    ):
        from app.worker.executor import execute_task_step
        await execute_task_step(sample_job)

    # Key should be marked exhausted, execution paused
    assert api_key2.status == APIKeyStatus.exhausted
    assert execution2.status == TaskExecutionStatus.paused_exhausted
    notify_exhausted.assert_awaited_once_with(ids["user"], ids["api_key"])


@pytest.mark.asyncio
async def test_execute_provider_error(ids, sample_job):
    """ProviderError → execution marked failed, notify_task_failed called."""
    from ai_providers.base import ProviderError

    execution = _make_execution(
        ids["execution"], ids["api_key"], ids["task_version"], ids["user"]
    )
    prompt_vid = ids["prompt_version"]
    task_version = _make_task_version([prompt_vid])
    prompt_version = _make_prompt_version()
    api_key = _make_api_key()

    execution2 = _make_execution(
        ids["execution"], ids["api_key"], ids["task_version"], ids["user"]
    )

    async def _get_primary(model_class, pk):
        from app.models import TaskExecution, TaskVersion, PromptVersion, APIKey
        if model_class is TaskExecution:
            return execution
        if model_class is TaskVersion:
            return task_version
        if model_class is PromptVersion:
            return prompt_version
        if model_class is APIKey:
            return api_key
        return None

    async def _get_secondary(model_class, pk):
        from app.models import TaskExecution
        if model_class is TaskExecution:
            return execution2
        return None

    session1 = AsyncMock()
    session1.get = _get_primary
    session1.add = MagicMock()
    session1.commit = AsyncMock()

    session2 = AsyncMock()
    session2.get = _get_secondary
    session2.add = MagicMock()
    session2.commit = AsyncMock()

    sessions = [session1, session2]
    idx = 0

    @asynccontextmanager
    async def _factory():
        nonlocal idx
        current = sessions[idx]
        idx += 1
        yield current

    notify_failed = AsyncMock()

    with (
        patch("app.worker.executor.async_session_factory", side_effect=_factory),
        patch("app.worker.executor.user_can_use_api_key", new=AsyncMock(return_value=True)),
        patch("app.worker.executor.acquire_lock", new=AsyncMock(return_value=True)),
        patch("app.worker.executor.release_lock", new=AsyncMock()),
        patch("app.worker.executor.decrypt_api_key", return_value="sk-plaintext"),
        patch("app.worker.executor.ai_execute", new=AsyncMock(side_effect=ProviderError("upstream error"))),
        patch("app.worker.executor.notify_task_failed", new=notify_failed),
    ):
        from app.worker.executor import execute_task_step
        await execute_task_step(sample_job)

    assert execution2.status == TaskExecutionStatus.failed
    notify_failed.assert_awaited_once()
    call_args = notify_failed.call_args
    assert call_args[0][0] == ids["user"]
    assert call_args[0][1] == ids["execution"]
    assert "upstream error" in call_args[1]["reason"]


@pytest.mark.asyncio
async def test_execute_permission_denied(ids, sample_job):
    """user_can_use_api_key returns False → execution marked failed immediately."""
    execution = _make_execution(
        ids["execution"], ids["api_key"], ids["task_version"], ids["user"]
    )
    prompt_vid = ids["prompt_version"]
    task_version = _make_task_version([prompt_vid])
    prompt_version = _make_prompt_version()
    api_key = _make_api_key()
    session = _make_mock_session(execution, task_version, prompt_version, api_key)

    notify_failed = AsyncMock()

    with (
        patch("app.worker.executor.async_session_factory", side_effect=lambda: _session_ctx(session)),
        patch("app.worker.executor.user_can_use_api_key", new=AsyncMock(return_value=False)),
        patch("app.worker.executor.acquire_lock", new=AsyncMock()) as mock_acquire,
        patch("app.worker.executor.notify_task_failed", new=notify_failed),
    ):
        from app.worker.executor import execute_task_step
        await execute_task_step(sample_job)

    # Lock should never be acquired when permission is denied
    mock_acquire.assert_not_awaited()
    assert execution.status == TaskExecutionStatus.failed
    notify_failed.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_idempotency_guard(ids, sample_job):
    """Already-completed execution is skipped without any processing."""
    execution = _make_execution(
        ids["execution"], ids["api_key"], ids["task_version"], ids["user"],
        status=TaskExecutionStatus.completed,
    )
    prompt_vid = ids["prompt_version"]
    task_version = _make_task_version([prompt_vid])
    prompt_version = _make_prompt_version()
    api_key = _make_api_key()
    session = _make_mock_session(execution, task_version, prompt_version, api_key)

    with (
        patch("app.worker.executor.async_session_factory", side_effect=lambda: _session_ctx(session)),
        patch("app.worker.executor.user_can_use_api_key", new=AsyncMock()) as mock_perm,
        patch("app.worker.executor.ai_execute", new=AsyncMock()) as mock_ai,
    ):
        from app.worker.executor import execute_task_step
        await execute_task_step(sample_job)

    # Neither permission check nor AI call should happen
    mock_perm.assert_not_awaited()
    mock_ai.assert_not_awaited()
