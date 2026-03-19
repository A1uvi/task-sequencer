# app — Application Package

## Purpose
Core application package containing all modules for the FastAPI backend.

## Submodules
- `models/` — SQLAlchemy ORM models and enums
- `schemas/` — Pydantic v2 request/response schemas
- `api/routes/` — FastAPI route handlers (one file per resource)
- `core/` — config, security (JWT), encryption (AES-256)
- `services/` — business logic: permissions, audit logging, notifications
- `worker/` — task queue, distributed lock, step executor, retry scheduler

## Import Conventions
Import models via `from app.models import ModelName`.
Import schemas via `from app.schemas.module import SchemaName`.
Import core utilities via `from app.core.module import function`.
