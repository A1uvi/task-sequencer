# Backend

## Stack
Python 3.11, FastAPI 0.111+, SQLAlchemy 2.0 (async), Alembic, Pydantic v2

## Structure
- `main.py` — FastAPI app entry point. Registers all routers and middleware.
- `app/models/` — SQLAlchemy ORM models and enums
- `app/schemas/` — Pydantic v2 request/response schemas
- `app/api/routes/` — FastAPI route handlers (one file per resource)
- `app/core/` — config, security (JWT), encryption (AES-256)
- `app/services/` — business logic: permissions, audit logging, notifications
- `app/worker/` — task queue, distributed lock, step executor, retry scheduler
- `ai_providers/` — unified AI provider abstraction (OpenAI, Claude, Gemini)
- `migrations/` — Alembic migration scripts

## Running
```bash
uvicorn main:app --reload          # API server
python -m app.worker.main          # Background worker (separate terminal)
```

## Testing
```bash
pytest                             # all tests
pytest tests/test_api/             # API tests only
pytest tests/test_worker/          # worker tests only
```

## Environment
All config via environment variables. See `../.env.example`.
Loaded via `app/core/config.py` using pydantic-settings.

## Critical Rules
- No sync database calls anywhere
- Never log or return decrypted API keys
- Permission checks must happen before decryption
- Worker and API server are separate OS processes
