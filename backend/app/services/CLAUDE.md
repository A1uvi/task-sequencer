# app/services — Business Logic Services

## Purpose
Stateless service functions called by both routes and the worker.
No direct HTTP concerns here — no Request/Response objects.

## Files
- `permissions.py` — access control checks (see Contract 5 in root CLAUDE.md)
- `audit.py` — append-only audit log writer
- `notifications.py` — email trigger functions (see Contract 7 in root CLAUDE.md)
- `notification_prefs.py` — reads User.notification_preferences before sending

## Permission Check Rules
Always check permissions BEFORE any decryption or destructive operation.
`user_can_use_api_key()` must verify all four access paths:
  1. user is direct owner
  2. user is in shared_with_users[]
  3. user's team owns the key
  4. user's team is in shared_with_teams[]

## Audit Log
Every key usage, sharing change, and task execution start must be logged.
Schema: user_id, event_type (str), resource_id (UUID), metadata (JSONB), created_at

## Notification Flow
notifications.py always calls `notification_prefs.should_notify()` before sending.
Email send failures must be caught and logged — never raise to caller.
