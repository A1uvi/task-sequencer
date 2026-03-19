import json
import uuid

import redis.asyncio as redis

from app.worker.jobs import ExecuteTaskStepJob
from app.core.config import settings

QUEUE_KEY = "task_execution_queue"


async def get_redis() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


async def enqueue_job(job: ExecuteTaskStepJob) -> None:
    """Push job to left of list (newest first in LPUSH/BRPOP pattern)."""
    r = await get_redis()
    payload = json.dumps({
        "task_execution_id": str(job.task_execution_id),
        "step_index": job.step_index,
        "api_key_id": str(job.api_key_id),
    })
    await r.lpush(QUEUE_KEY, payload)
    await r.aclose()


async def dequeue_job(timeout: int = 5) -> ExecuteTaskStepJob | None:
    """Block up to `timeout` seconds for a job. Returns None on timeout."""
    r = await get_redis()
    result = await r.brpop(QUEUE_KEY, timeout=timeout)
    await r.aclose()
    if result is None:
        return None
    _, payload = result
    data = json.loads(payload)
    return ExecuteTaskStepJob(
        task_execution_id=uuid.UUID(data["task_execution_id"]),
        step_index=data["step_index"],
        api_key_id=uuid.UUID(data["api_key_id"]),
    )
