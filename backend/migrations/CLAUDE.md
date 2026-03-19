# migrations — Alembic Database Migrations

## Purpose
Version-controlled database schema changes using Alembic with async SQLAlchemy.

## Running Migrations
```bash
alembic upgrade head          # apply all migrations
alembic revision --autogenerate -m "description"   # generate new migration
alembic downgrade -1          # roll back one step
```

## Rules
- Never modify a migration file after it has been applied to any environment
- Always generate migrations from model changes, never write them by hand
- Migration 0001 is the baseline for the full schema

## env.py
Configured for async SQLAlchemy. Imports all models from `app.models` so
autogenerate can detect schema changes. DATABASE_URL comes from environment.
