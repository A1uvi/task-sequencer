# tests/test_api — API Route Tests

## Purpose
Integration tests for all FastAPI routes using httpx.AsyncClient.

## Setup
See parent `tests/CLAUDE.md` and `conftest.py` for fixtures.

## Pattern
Each test file maps 1:1 to a route file in `app/api/routes/`.
Test happy path, permission errors (403), and validation errors (422).
