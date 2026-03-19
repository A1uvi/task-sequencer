"""
Tests for /task-executions endpoints.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


def _make_execution(user_id):
    exec_ = MagicMock()
    exec_.id = uuid.uuid4()
    exec_.task_version_id = uuid.uuid4()
    exec_.api_key_id = uuid.uuid4()
    exec_.status = "queued"
    exec_.current_step_index = 0
    exec_.last_prompt_version_id = None
    exec_.step_outputs = {}
    exec_.created_by = user_id
    exec_.created_at = datetime.now(timezone.utc)
    exec_.updated_at = datetime.now(timezone.utc)
    return exec_


@pytest.mark.asyncio
async def test_list_task_executions_unauthenticated(unauthenticated_client: AsyncClient):
    """GET /task-executions without auth returns 401."""
    response = await unauthenticated_client.get("/task-executions")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_task_execution_unauthenticated(unauthenticated_client: AsyncClient):
    """GET /task-executions/{id} without auth returns 401."""
    response = await unauthenticated_client.get(f"/task-executions/{uuid.uuid4()}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_task_execution_permission_denied(client: AsyncClient, mock_user):
    """GET /task-executions/{id} returns 403 when user is not the creator."""
    execution = _make_execution(user_id=uuid.uuid4())  # different user

    mock_session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = execution
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.get(f"/task-executions/{execution.id}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_task_executions_happy_path(client: AsyncClient, mock_user):
    """GET /task-executions returns a list for the current user."""
    mock_session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.get("/task-executions")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_initiate_task_execution_permission_denied_on_api_key(
    client: AsyncClient, mock_user
):
    """POST /task-executions returns 403 when user cannot use the API key."""
    task_version = MagicMock()
    task_version.id = uuid.uuid4()

    mock_session = AsyncMock()
    tv_result = MagicMock()
    tv_result.scalar_one_or_none.return_value = task_version
    # Permission check: api key lookup
    api_key_result = MagicMock()
    api_key_result.scalar_one_or_none.return_value = None  # api key not found → False
    teams_result = MagicMock()
    teams_result.scalars.return_value.all.return_value = []

    mock_session.execute = AsyncMock(
        side_effect=[tv_result, api_key_result, teams_result]
    )
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.post(
            "/task-executions",
            json={
                "task_version_id": str(task_version.id),
                "api_key_id": str(uuid.uuid4()),
            },
        )

    assert response.status_code == 403
