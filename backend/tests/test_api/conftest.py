"""
Shared fixtures for API integration tests.

Uses httpx.AsyncClient with ASGITransport to make requests against the
FastAPI app in-process, with the get_current_user dependency overridden so
tests don't need real JWTs.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.security import get_current_user
from app.models import User
from main import app


@pytest.fixture
def mock_user() -> User:
    """A fake User instance returned by the overridden auth dependency."""
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        notification_preferences={},
    )


@pytest_asyncio.fixture
async def client(mock_user: User) -> AsyncClient:
    """AsyncClient with auth dependency overridden to return mock_user."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def unauthenticated_client() -> AsyncClient:
    """AsyncClient with NO auth override — tests unauthenticated requests."""
    # Ensure overrides are clean
    app.dependency_overrides.clear()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
