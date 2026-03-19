# app/worker — Task Queue, Executor, Retry Scheduler

## Purpose
Background worker process. Consumes jobs from Redis queue, executes task steps
against AI providers, manages distributed locking, and handles quota exhaustion.

## Files
- `jobs.py` — ExecuteTaskStepJob dataclass (Contract 6)
- `queue.py` — enqueue_job() / dequeue_job() using Redis
- `locks.py` — distributed lock per api_key_id using Redis SET NX PX
- `executor.py` — core step execution logic (see execution flow below)
- `retry_scheduler.py` — APScheduler job that probes exhausted keys and resumes tasks
- `main.py` — worker entrypoint, infinite dequeue loop with graceful SIGTERM shutdown

## Running the Worker
```bash
python -m app.worker.main
```
This is a SEPARATE process from the API server. Both must run simultaneously.

## Execution Flow (executor.py)
1. Load TaskExecution — verify not already failed/completed
2. Load prompt content from PromptVersion at current_step_index
3. Check user_can_use_api_key() — fail fast if False
4. Acquire Redis lock for api_key_id (requeue with 5s delay if unavailable)
5. Decrypt API key in memory
6. Mark execution status = running
7. Call ai_providers.execute()
8. On QuotaExhaustedError → mark key exhausted, pause execution, notify, release lock
9. On ProviderError → mark execution failed, notify, release lock
10. On success → store Conversation, increment step, release lock, enqueue next step or complete

## Concurrency Rule (Critical)
The Redis lock must be held for the MINIMUM duration.
Acquire just before the AI call. Release immediately after.
Never hold the lock across DB writes or queue operations.

## Retry Backoff Schedule
Attempt 1 → 15 min, Attempt 2 → 1 hour, Attempt 3 → 6 hours, Attempt 4+ → 24 hours
Backoff state stored in Redis key: `retry_backoff:{api_key_id}`

## Testing the Worker in Isolation
Mock `ai_providers.execute` and `decrypt_api_key`.
Use a real Redis instance (or fakeredis) for lock and queue tests.
See `tests/test_worker/`.
