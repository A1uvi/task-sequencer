# app/api/routes — FastAPI Route Handlers

## Purpose
HTTP endpoints. One file per resource domain.

## Files
- `auth.py` — POST /auth/register, POST /auth/login
- `folders.py` — CRUD for Folder
- `prompts.py` — CRUD for Prompt + PromptVersion management
- `tasks.py` — CRUD for Task + TaskVersion management
- `api_keys.py` — API key CRUD + sharing
- `task_executions.py` — initiate + poll task executions
- `conversations.py` — read-only conversation access
- `search.py` — full-text search across prompts/tasks/conversations

## Rules
- Every route that reads/writes a resource must call the relevant permission check FIRST
- Return 403 (not 404) when a resource exists but the user lacks permission
- All list endpoints must support `limit` and `offset` query params
- Routes never call `decrypt_api_key()` directly — that is the worker's responsibility
- Routes never call `ai_providers.execute()` — all AI calls go through the worker

## Auth
All routes (except /auth/*) require a valid JWT.
Use the `get_current_user` dependency from `app.core.security`.

## Adding a New Route
1. Create or edit the relevant file in this directory
2. Register the router in `backend/main.py`
3. Add corresponding schema to `app/schemas/`
4. Write tests in `tests/test_api/`
