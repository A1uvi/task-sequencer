# tests/test_worker — Worker Unit Tests

## Purpose
Unit tests for the task queue, executor, distributed lock, and retry scheduler.

## Mocking Strategy
- Mock `ai_providers.execute` using `unittest.mock.AsyncMock`
- Mock `decrypt_api_key` to return a test key
- Use `fakeredis` for Redis-dependent tests

## Key Test Scenarios
- Executor: happy path step completion, quota exhaustion, provider error
- Lock: acquire success, contention (lock held), timeout
- Retry: backoff schedule progression, resume on key refill
