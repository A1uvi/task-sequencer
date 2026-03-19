"""
Tests for GET /search endpoint.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_search_unauthenticated(unauthenticated_client: AsyncClient):
    """GET /search without auth returns 401."""
    response = await unauthenticated_client.get("/search", params={"q": "hello"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_search_missing_query_returns_422(client: AsyncClient):
    """GET /search without q param returns 422 validation error."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.get("/search")  # missing q param

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_returns_list(client: AsyncClient):
    """GET /search with valid q returns a list."""
    mock_session = AsyncMock()
    teams_result = MagicMock()
    teams_result.scalars.return_value.all.return_value = []
    prompts_result = MagicMock()
    prompts_result.scalars.return_value.all.return_value = []
    tasks_result = MagicMock()
    tasks_result.scalars.return_value.all.return_value = []

    mock_session.execute = AsyncMock(
        side_effect=[teams_result, prompts_result, tasks_result]
    )
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.get("/search", params={"q": "hello"})

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_search_type_prompt_filter(client: AsyncClient):
    """GET /search?type=prompt only searches prompts, not tasks."""
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
        response = await client.get("/search", params={"q": "test", "type": "prompt"})

    assert response.status_code == 200
    body = response.json()
    assert all(item["type"] == "prompt" for item in body)


@pytest.mark.asyncio
async def test_search_result_schema(client: AsyncClient):
    """Search results contain expected fields: type, id, title, snippet, created_at."""
    from datetime import datetime, timezone

    mock_prompt = MagicMock()
    mock_prompt.id = uuid.uuid4()
    mock_prompt.title = "My Prompt"
    mock_prompt.created_at = datetime.now(timezone.utc)
    mock_prompt.visibility_type = "public"
    mock_prompt.created_by = uuid.uuid4()
    mock_prompt.folder_id = None

    mock_session = AsyncMock()
    teams_result = MagicMock()
    teams_result.scalars.return_value.all.return_value = []
    prompts_result = MagicMock()
    prompts_result.scalars.return_value.all.return_value = [mock_prompt]
    tasks_result = MagicMock()
    tasks_result.scalars.return_value.all.return_value = []

    mock_session.execute = AsyncMock(
        side_effect=[teams_result, prompts_result, tasks_result]
    )
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.get("/search", params={"q": "prompt"})

    assert response.status_code == 200
    body = response.json()
    if body:
        item = body[0]
        assert "type" in item
        assert "id" in item
        assert "title" in item
        assert "snippet" in item
        assert "created_at" in item
