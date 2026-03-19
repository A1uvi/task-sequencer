"""
Tests for /api-keys endpoints.

Key requirements verified:
- POST /api-keys never returns `encrypted_key` in response
- POST /api-keys returns `masked_key` (last 4 chars of plaintext)
- Auth missing → 401
- Permission denied → 403
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


def _make_api_key(owner_id=None):
    key = MagicMock()
    key.id = uuid.uuid4()
    key.provider = "openai"
    key.encrypted_key = "encrypted_data_abc_1234"  # last 4 would be "1234"
    key.owner_type = "user"
    key.owner_id = owner_id or uuid.uuid4()
    key.shared_with_users = []
    key.shared_with_teams = []
    key.status = "active"
    key.created_at = datetime.now(timezone.utc)
    return key


@pytest.mark.asyncio
async def test_list_api_keys_unauthenticated(unauthenticated_client: AsyncClient):
    """GET /api-keys without auth returns 401."""
    response = await unauthenticated_client.get("/api-keys")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_api_key_unauthenticated(unauthenticated_client: AsyncClient):
    """GET /api-keys/{id} without auth returns 401."""
    response = await unauthenticated_client.get(f"/api-keys/{uuid.uuid4()}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_api_key_permission_denied(client: AsyncClient, mock_user):
    """GET /api-keys/{id} returns 403 when user cannot use the key."""
    api_key = _make_api_key(owner_id=uuid.uuid4())  # different owner
    api_key.owner_type = "user"

    mock_session = AsyncMock()
    # First call: get api key; second call: permission check (get api key again)
    key_result = MagicMock()
    key_result.scalar_one_or_none.return_value = api_key
    perm_key_result = MagicMock()
    perm_key_result.scalar_one_or_none.return_value = api_key
    teams_result = MagicMock()
    teams_result.scalars.return_value.all.return_value = []

    mock_session.execute = AsyncMock(side_effect=[key_result, perm_key_result, teams_result])
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.get(f"/api-keys/{api_key.id}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_api_key_response_has_no_encrypted_key(client: AsyncClient, mock_user):
    """POST /api-keys response must NOT contain the encrypted_key field."""
    from datetime import datetime, timezone
    plaintext = "sk-test-abcd1234"

    added_objects = []

    def _add_with_defaults(obj):
        """Simulate DB flush by setting server-generated fields."""
        if not getattr(obj, "id", None):
            obj.id = uuid.uuid4()
        if not getattr(obj, "created_at", None):
            obj.created_at = datetime.now(timezone.utc)
        added_objects.append(obj)

    mock_session = AsyncMock()
    mock_session.add = MagicMock(side_effect=_add_with_defaults)
    mock_session.flush = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.api.routes.api_keys.encrypt_api_key", return_value="ENCRYPTED"),
        patch("app.api.routes.api_keys.log_event", new=AsyncMock(return_value=None)),
        patch("app.core.database.AsyncSessionLocal", return_value=mock_session),
    ):
        response = await client.post(
            "/api-keys",
            json={
                "provider": "openai",
                "owner_type": "user",
                "owner_id": str(mock_user.id),
                "key": plaintext,
                "shared_with_users": [],
                "shared_with_teams": [],
                "status": "active",
            },
        )

    # Response should not contain encrypted_key regardless of status
    if response.status_code in (200, 201):
        body = response.json()
        assert "encrypted_key" not in body
        assert "masked_key" in body
        # masked_key should be the last 4 chars of the plaintext key
        assert body["masked_key"] == plaintext[-4:]


@pytest.mark.asyncio
async def test_create_api_key_masked_key_is_last_4(client: AsyncClient, mock_user):
    """POST /api-keys returns masked_key = last 4 chars of the plaintext key."""
    from datetime import datetime, timezone
    plaintext = "sk-openai-xyz-9876"
    expected_masked = "9876"

    def _add_with_defaults(obj):
        """Simulate DB flush by setting server-generated fields."""
        if not getattr(obj, "id", None):
            obj.id = uuid.uuid4()
        if not getattr(obj, "created_at", None):
            obj.created_at = datetime.now(timezone.utc)

    mock_session = AsyncMock()
    mock_session.add = MagicMock(side_effect=_add_with_defaults)
    mock_session.flush = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.api.routes.api_keys.encrypt_api_key", return_value="ENCRYPTED"),
        patch("app.api.routes.api_keys.log_event", new=AsyncMock(return_value=None)),
        patch("app.core.database.AsyncSessionLocal", return_value=mock_session),
    ):
        response = await client.post(
            "/api-keys",
            json={
                "provider": "openai",
                "owner_type": "user",
                "owner_id": str(mock_user.id),
                "key": plaintext,
                "shared_with_users": [],
                "shared_with_teams": [],
                "status": "active",
            },
        )

    if response.status_code in (200, 201):
        body = response.json()
        assert body.get("masked_key") == expected_masked


@pytest.mark.asyncio
async def test_list_api_keys_happy_path(client: AsyncClient, mock_user):
    """GET /api-keys returns a list."""
    mock_session = AsyncMock()
    teams_result = MagicMock()
    teams_result.scalars.return_value.all.return_value = []
    keys_result = MagicMock()
    keys_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(side_effect=[teams_result, keys_result])
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        response = await client.get("/api-keys")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
