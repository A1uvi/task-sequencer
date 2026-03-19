"""
Tests for /tasks endpoints.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_tasks_happy_path(client: AsyncClient):
    """GET /tasks returns a list."""
    mock_session = AsyncMock()
    teams_result = MagicMock()
    teams_result.scalars.return_value.all.return_value = []
    tasks_result = MagicMock()
    tasks_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(side_effect=[teams_result, tasks_result])
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.get("/tasks")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_tasks_unauthenticated(unauthenticated_client: AsyncClient):
    """GET /tasks without auth returns 401."""
    response = await unauthenticated_client.get("/tasks")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient):
    """GET /tasks/{id} for non-existent task returns 404."""
    mock_session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.get(f"/tasks/{uuid.uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_task_permission_denied(client: AsyncClient, mock_user):
    """GET /tasks/{id} returns 403 for private task by another user."""
    task = MagicMock()
    task.id = uuid.uuid4()
    task.visibility_type = "private"
    task.created_by = uuid.uuid4()  # different user
    task.folder_id = None

    mock_session = AsyncMock()
    task_result = MagicMock()
    task_result.scalar_one_or_none.return_value = task
    perm_task_result = MagicMock()
    perm_task_result.scalar_one_or_none.return_value = task

    mock_session.execute = AsyncMock(side_effect=[task_result, perm_task_result])
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.get(f"/tasks/{task.id}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_task_owner_only(client: AsyncClient, mock_user):
    """DELETE /tasks/{id} by non-owner returns 403."""
    task = MagicMock()
    task.id = uuid.uuid4()
    task.created_by = uuid.uuid4()  # not mock_user

    mock_session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = task
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.delete(f"/tasks/{task.id}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_task_owner_only(client: AsyncClient, mock_user):
    """PATCH /tasks/{id} by non-owner returns 403."""
    task = MagicMock()
    task.id = uuid.uuid4()
    task.created_by = uuid.uuid4()  # not mock_user

    mock_session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = task
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.patch(
            f"/tasks/{task.id}", json={"title": "New Title"}
        )

    assert response.status_code == 403
