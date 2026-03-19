from apscheduler.schedulers.asyncio import AsyncIOScheduler
import redis.asyncio as redis

from app.core.config import settings
from app.core.database import async_session_factory
from app.worker.queue import enqueue_job
from app.worker.jobs import ExecuteTaskStepJob

RETRY_BACKOFF_KEY_PREFIX = "retry_backoff:"
# Backoff schedule: attempt → delay minutes
BACKOFF_SCHEDULE = {1: 15, 2: 60, 3: 360}
DEFAULT_BACKOFF_MINUTES = 24 * 60  # 24 hours for attempt 4+


async def get_backoff_minutes(api_key_id: str) -> int:
    r = redis.from_url(settings.redis_url, decode_responses=True)
    attempt_str = await r.get(f"{RETRY_BACKOFF_KEY_PREFIX}{api_key_id}")
    await r.aclose()
    attempt = int(attempt_str or "0") + 1
    return BACKOFF_SCHEDULE.get(attempt, DEFAULT_BACKOFF_MINUTES)


async def increment_backoff_attempt(api_key_id: str) -> None:
    r = redis.from_url(settings.redis_url, decode_responses=True)
    key = f"{RETRY_BACKOFF_KEY_PREFIX}{api_key_id}"
    attempt_str = await r.get(key)
    attempt = int(attempt_str or "0") + 1
    await r.set(key, str(attempt), ex=7 * 24 * 3600)  # expire after 7 days
    await r.aclose()


async def clear_backoff(api_key_id: str) -> None:
    r = redis.from_url(settings.redis_url, decode_responses=True)
    await r.delete(f"{RETRY_BACKOFF_KEY_PREFIX}{api_key_id}")
    await r.aclose()


async def check_and_resume_paused_executions() -> None:
    """
    Periodic job: scan for TaskExecutions with status=paused_exhausted.
    For each, check if the APIKey is now active.
    If active, re-enqueue the next step and clear backoff counter.
    """
    from app.models import TaskExecution, APIKey
    from app.models.enums import TaskExecutionStatus, APIKeyStatus
    from sqlalchemy import select

    async with async_session_factory() as db:
        result = await db.execute(
            select(TaskExecution).where(
                TaskExecution.status == TaskExecutionStatus.paused_exhausted
            )
        )
        paused = result.scalars().all()

        for execution in paused:
            key_result = await db.get(APIKey, execution.api_key_id)
            if key_result and key_result.status == APIKeyStatus.active:
                # Re-enqueue
                await enqueue_job(ExecuteTaskStepJob(
                    task_execution_id=execution.id,
                    step_index=execution.current_step_index,
                    api_key_id=execution.api_key_id,
                ))
                await clear_backoff(str(execution.api_key_id))


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_and_resume_paused_executions,
        "interval",
        minutes=15,
        id="resume_paused_executions",
    )
    return scheduler
