"""
Shared pytest fixtures for the backend test suite.

asyncio_mode = "auto" is configured in pyproject.toml (or pytest.ini).
Each test that uses `async_session` gets a fresh transaction that is rolled
back after the test, so tests are isolated without re-creating the schema.
"""

import os
import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Use an in-process SQLite database for speed.
# Override with TEST_DATABASE_URL env var to use a real Postgres instance.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///./test_db.sqlite",
)

from app.models.base import Base

# Import all models so their tables are registered on Base.metadata
import app.models  # noqa: F401


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test engine and the full schema once per session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
        if TEST_DATABASE_URL.startswith("sqlite")
        else {},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(test_engine) -> AsyncSession:
    """
    Yield an AsyncSession that is rolled back after each test.
    This keeps tests isolated without re-building the schema.
    """
    async_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with test_engine.connect() as connection:
        await connection.begin()
        async with async_session_factory(bind=connection) as session:
            yield session
        await connection.rollback()


@pytest.fixture
def test_client():
    """
    Stub fixture for the FastAPI test client.
    Agent 4 will wire the actual FastAPI `app` here.
    Usage (once Agent 4 is complete):

        from main import app
        from httpx import AsyncClient
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    """
    # Placeholder — return None until Agent 4 registers routes
    return None
