# app/models — SQLAlchemy ORM Models

## Purpose
Defines all database tables as SQLAlchemy 2.0 async ORM models.
This is the single source of truth for the data model.
All other backend modules import models from here.

## Files
- `base.py` — Base class, UUIDMixin (id as UUID PK), TimestampMixin (created_at/updated_at)
- `enums.py` — VisibilityType, APIKeyOwnerType, APIKeyStatus, TaskExecutionStatus
- `user.py`, `team.py`, `folder.py`, `prompt.py`, `prompt_version.py`
- `conversation.py`, `api_key.py`, `task.py`, `task_version.py`, `task_execution.py`
- `__init__.py` — exports all models and enums

## Immutability Rules
PromptVersion, TaskVersion, and Conversation have NO `updated_at` field.
These records must never be modified after creation.

## Indexes
Required indexes: Prompt.folder_id, Task.folder_id, TaskExecution.status,
APIKey.owner_id, PromptVersion.prompt_id, TaskVersion.task_id

## Modifying the Schema
Always create a new Alembic migration in `../../migrations/`.
Never modify a migration that has already been applied.

## Testing
Import models in tests via `from app.models import User, Prompt` etc.
Use an in-memory SQLite or test Postgres DB — see `tests/conftest.py`.
