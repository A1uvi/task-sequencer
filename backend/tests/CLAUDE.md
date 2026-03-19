# tests — Backend Test Suite

## Structure
- `conftest.py` — shared fixtures: async test DB, test client, mock current user
- `test_api/` — route-level integration tests using httpx.AsyncClient
- `test_worker/` — worker unit tests with mocked AI provider and Redis

## Running
```bash
pytest                          # all tests
pytest tests/test_api/          # API tests only
pytest tests/test_worker/       # worker tests only
pytest -k "test_permissions"    # filter by name
```

## Test Database
Tests use a separate Postgres DB (TEST_DATABASE_URL env var) or SQLite for speed.
Each test function gets a clean DB via transaction rollback in the fixture.

## Mocking AI Providers
Never make real API calls in tests.
Use `unittest.mock.AsyncMock` to mock `ai_providers.execute`.

## Mocking Email
Use `unittest.mock.patch` on `app.services.email.send_email`.
