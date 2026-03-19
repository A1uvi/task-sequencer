"""
Tests for /prompts endpoints.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_prompts_happy_path(client: AsyncClient):
    """GET /prompts returns a list."""
    mock_session = AsyncMock()
    teams_result = MagicMock()
    teams_result.scalars.return_value.all.return_value = []
    prompts_result = MagicMock()
    prompts_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(side_effect=[teams_result, prompts_result])
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.get("/prompts")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_prompts_unauthenticated(unauthenticated_client: AsyncClient):
    """GET /prompts without auth returns 401."""
    response = await unauthenticated_client.get("/prompts")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_prompt_not_found(client: AsyncClient):
    """GET /prompts/{id} for non-existent prompt returns 404."""
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
        response = await client.get(f"/prompts/{uuid.uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_prompt_permission_denied(client: AsyncClient, mock_user):
    """GET /prompts/{id} returns 403 when user lacks access."""
    prompt = MagicMock()
    prompt.id = uuid.uuid4()
    prompt.visibility_type = "private"
    prompt.created_by = uuid.uuid4()  # different user
    prompt.folder_id = None

    mock_session = AsyncMock()
    prompt_result = MagicMock()
    prompt_result.scalar_one_or_none.return_value = prompt

    # permissions check: get prompt again (user_can_access_prompt -> get prompt)
    perm_prompt_result = MagicMock()
    perm_prompt_result.scalar_one_or_none.return_value = prompt

    mock_session.execute = AsyncMock(side_effect=[prompt_result, perm_prompt_result])
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.get(f"/prompts/{prompt.id}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_prompt_owner_only(client: AsyncClient, mock_user):
    """DELETE /prompts/{id} by non-owner returns 403."""
    prompt = MagicMock()
    prompt.id = uuid.uuid4()
    prompt.created_by = uuid.uuid4()  # not mock_user

    mock_session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = prompt
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.delete(f"/prompts/{prompt.id}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_prompt_owner_only(client: AsyncClient, mock_user):
    """PATCH /prompts/{id} by non-owner returns 403."""
    prompt = MagicMock()
    prompt.id = uuid.uuid4()
    prompt.created_by = uuid.uuid4()  # not mock_user

    mock_session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = prompt
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.patch(
            f"/prompts/{prompt.id}", json={"title": "New Title"}
        )

    assert response.status_code == 403
