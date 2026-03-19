"""
Tests for /folders endpoints.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


def _make_folder(user_id=None):
    folder = MagicMock()
    folder.id = uuid.uuid4()
    folder.name = "Test Folder"
    folder.visibility_type = "public"
    folder.team_ids = []
    folder.created_by = user_id or uuid.uuid4()
    folder.created_at = "2024-01-01T00:00:00Z"
    folder.updated_at = "2024-01-01T00:00:00Z"
    folder.model_fields = {}
    return folder


@pytest.mark.asyncio
async def test_list_folders_happy_path(client: AsyncClient):
    """GET /folders returns a list (may be empty)."""
    with patch("app.api.routes.folders.get_db"):
        mock_session = AsyncMock()
        teams_result = MagicMock()
        teams_result.scalars.return_value.all.return_value = []
        folders_result = MagicMock()
        folders_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(side_effect=[teams_result, folders_result])
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
            response = await client.get("/folders")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_folders_unauthenticated(unauthenticated_client: AsyncClient):
    """GET /folders without auth returns 401."""
    response = await unauthenticated_client.get("/folders")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_folder_not_found(client: AsyncClient, mock_user):
    """GET /folders/{id} for a non-existent folder returns 404."""
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
        response = await client.get(f"/folders/{uuid.uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_folder_permission_denied(client: AsyncClient, mock_user):
    """GET /folders/{id} returns 403 when user cannot access folder."""
    folder = _make_folder(user_id=uuid.uuid4())  # different owner

    mock_session = AsyncMock()
    # First call: get folder; second call: get user teams (for permissions)
    folder_result = MagicMock()
    folder_result.scalar_one_or_none.return_value = folder
    teams_result = MagicMock()
    teams_result.scalars.return_value.all.return_value = []
    private_folder_result = MagicMock()
    private_folder_result.scalar_one_or_none.return_value = folder

    mock_session.execute = AsyncMock(side_effect=[folder_result, teams_result])
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    # Set folder to private so user (not owner) gets 403
    folder.visibility_type = "private"

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.get(f"/folders/{folder.id}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_folder_unauthenticated(unauthenticated_client: AsyncClient):
    """POST /folders without auth returns 401."""
    response = await unauthenticated_client.post(
        "/folders",
        json={"name": "My Folder", "visibility_type": "private", "team_ids": []},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_folder_owner_only(client: AsyncClient, mock_user):
    """DELETE /folders/{id} by non-owner returns 403."""
    folder = _make_folder(user_id=uuid.uuid4())  # different owner

    mock_session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = folder
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.delete(f"/folders/{folder.id}")

    assert response.status_code == 403
