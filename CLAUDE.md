# AI Workflow Platform — Root

## Project Overview
Production-grade AI workflow platform. FastAPI backend + React frontend.
Allows users to save prompts, build multi-step tasks, and execute them
using their own AI provider API keys — all server-side, with encryption at rest.

## Repository Layout
- `backend/` — Python FastAPI application, worker service, AI provider abstraction
- `frontend/` — React 18 + TypeScript SPA
- `docker-compose.yml` — local dev environment (postgres, redis, api, worker)
- `.env.example` — all required environment variables with descriptions
- `PROGRESS.md` — execution checkpoint for multi-agent builds and resumption

## Running Locally
```bash
cp .env.example .env          # fill in values
docker compose up             # starts postgres + redis
cd backend && uvicorn main:app --reload
cd backend && python -m app.worker.main
cd frontend && npm run dev
```

## Running Tests
```bash
cd backend && pytest
cd frontend && npm run test
```

## Key Architecture Decisions
- All AI calls are server-side only. Never client-side.
- API keys are AES-256-GCM encrypted at rest; decrypted in memory only.
- Concurrency is serialized per API key via distributed Redis lock.
- All prompt/task edits create immutable new versions — nothing is overwritten.
- Worker and API server are separate processes communicating via Redis queue.

## Adding a New AI Provider
See `backend/ai_providers/CLAUDE.md`.

## Deploying a Targeted Agent to Fix an Issue
1. Read `PROGRESS.md` to understand the current state of the codebase
2. Find the relevant subdirectory
3. Read that directory's `CLAUDE.md` for full local context
4. The agent has everything it needs to work in isolation from there

## Integration Notes (completed)

### Frontend API Layer
All frontend API files in `frontend/src/api/` use real Axios calls — no mock data remains.
Key details:
- Login (`/auth/login`) sends form-encoded data (`application/x-www-form-urlencoded`) because the backend uses FastAPI's `OAuth2PasswordRequestForm`. The `username` field must contain the email address.
- Register (`/auth/register`) sends query params (not JSON body) because the route declares `email` and `password` as plain function parameters, not a Pydantic model.
- API key creation (`POST /api-keys`) only sends `provider` and `key` fields — the backend handles encryption server-side. The response contains `masked_key` (last 4 chars of plaintext) and never `encrypted_key`.
- Search (`GET /search`) omits `type` param when set to `'all'` to avoid backend validation issues.
- All list endpoints accept `limit` and `offset` pagination params.

### Test Suite
Both test suites are fully green as of integration:
- **Frontend**: 47 tests across 8 files (`npm run test -- --run` from `frontend/`)
- **Backend**: 130 tests across all test files (`pytest` from `backend/` with env vars below)

Backend tests require these env vars:
```bash
DATABASE_URL="sqlite+aiosqlite:///./test_db.sqlite"
SECRET_KEY="test-secret-key-for-tests-only-32bytes!"
ENCRYPTION_KEY="dGVzdC1lbmNyeXB0aW9uLWtleS0zMmJ5dGVzISE="
```

### Critical Mocking Patterns for Backend Tests
- **FastAPI dependency override**: Use `app.dependency_overrides[get_db] = _mock_get_db` (not `unittest.mock.patch`) to override `Depends(get_db)` in route tests. `patch()` cannot intercept FastAPI's DI system.
- **Async context manager factories**: When a factory yields a session (e.g., `async_session_factory`), increment the session index BEFORE `yield` so nested calls inside the same context manager get the next session.
- **Module-level imports for patching**: Functions imported locally inside another function cannot be patched with `patch("module.function")` because the attribute does not exist at module scope. Move imports to module level.
- **SQLAlchemy statement validation**: Patching `select` to return a `MagicMock` causes `session.execute()` to raise `ArgumentError` because SQLAlchemy validates that the argument is a real SQL construct.
- **Pydantic model construction after flush**: `APIKey()` does not auto-populate `id` or `created_at` (SQLAlchemy sets them on flush). Simulate this in tests by adding a `side_effect` to `mock_session.add` that sets these fields.
