import asyncio
import logging
import uuid

from sqlalchemy import select

from ai_providers import execute as ai_execute, QuotaExhaustedError, ProviderError
from ai_providers.base import ProviderMessage
from app.core.encryption import decrypt_api_key
from app.services.permissions import user_can_use_api_key
from app.services.notifications import (
    notify_token_exhausted,
    notify_task_failed,
    notify_task_completed,
)
from app.worker.locks import acquire_lock, release_lock
from app.worker.queue import enqueue_job
from app.worker.jobs import ExecuteTaskStepJob
from app.models import TaskExecution, TaskVersion, PromptVersion, APIKey, Conversation
from app.models.enums import TaskExecutionStatus, APIKeyStatus
from app.core.database import async_session_factory

logger = logging.getLogger(__name__)


async def execute_task_step(job: ExecuteTaskStepJob) -> None:
    """Execute a single step of a task, following the full execution flow."""
    task_execution_id = job.task_execution_id
    step_index = job.step_index
    api_key_id = job.api_key_id

    async with async_session_factory() as db:
        # 1. Load TaskExecution — verify status is not failed/completed (idempotency guard)
        execution = await db.get(TaskExecution, task_execution_id)
        if execution is None:
            logger.error("TaskExecution %s not found", task_execution_id)
            return

        if execution.status in (
            TaskExecutionStatus.failed,
            TaskExecutionStatus.completed,
        ):
            logger.info(
                "TaskExecution %s already in terminal state %s — skipping",
                task_execution_id,
                execution.status,
            )
            return

        user_id: uuid.UUID = execution.created_by

        # 2. Load TaskVersion → get ordered_prompt_version_ids
        task_version = await db.get(TaskVersion, execution.task_version_id)
        if task_version is None:
            logger.error("TaskVersion %s not found", execution.task_version_id)
            execution.status = TaskExecutionStatus.failed
            await db.commit()
            return

        ordered_ids: list = task_version.ordered_prompt_version_ids
        total_steps = len(ordered_ids)

        if step_index >= total_steps:
            logger.error(
                "step_index %d out of range for TaskVersion %s (total steps: %d)",
                step_index,
                task_version.id,
                total_steps,
            )
            execution.status = TaskExecutionStatus.failed
            await db.commit()
            return

        # 3. Get PromptVersion at current_step_index
        prompt_version_id = ordered_ids[step_index]
        prompt_version = await db.get(PromptVersion, prompt_version_id)
        if prompt_version is None:
            logger.error("PromptVersion %s not found", prompt_version_id)
            execution.status = TaskExecutionStatus.failed
            await db.commit()
            return

        # 4. Check user_can_use_api_key() — mark failed and return if False
        has_permission = await user_can_use_api_key(user_id, api_key_id, db)
        if not has_permission:
            logger.warning(
                "User %s does not have permission to use APIKey %s",
                user_id,
                api_key_id,
            )
            execution.status = TaskExecutionStatus.failed
            await db.commit()
            await notify_task_failed(
                user_id,
                task_execution_id,
                reason="Permission denied: user cannot use the specified API key",
            )
            return

        # 5. Try to acquire Redis lock for api_key_id
        api_key_id_str = str(api_key_id)
        lock_acquired = False
        deadline = asyncio.get_event_loop().time() + 10.0
        poll_interval = 0.5

        while asyncio.get_event_loop().time() < deadline:
            if await acquire_lock(api_key_id_str):
                lock_acquired = True
                break
            await asyncio.sleep(poll_interval)

        if not lock_acquired:
            # Lock unavailable after 10s — requeue with 5s delay
            logger.warning(
                "Could not acquire lock for api_key_id=%s after 10s; requeueing job",
                api_key_id_str,
            )
            await asyncio.sleep(5)
            await enqueue_job(job)
            return

        # From this point on, we hold the lock. Release it in all code paths.
        try:
            # 6. Decrypt API key in memory
            api_key_record = await db.get(APIKey, api_key_id)
            if api_key_record is None:
                logger.error("APIKey %s not found in DB", api_key_id)
                execution.status = TaskExecutionStatus.failed
                await db.commit()
                return

            plaintext_key = decrypt_api_key(api_key_record.encrypted_key)
            provider = api_key_record.provider
            model = task_version.default_model

            # 7. Mark TaskExecution.status = running, commit
            execution.status = TaskExecutionStatus.running
            await db.commit()

            # 8. Build messages — include prior step outputs as context
            step_outputs: dict = execution.step_outputs or {}
            messages: list[ProviderMessage] = [
                ProviderMessage(role="user", content=prompt_version.content)
            ]

            # Prepend previous step outputs as assistant context
            for i in range(step_index):
                prev_output = step_outputs.get(str(i), {}).get("content", "")
                if prev_output:
                    messages.insert(-1, ProviderMessage(role="assistant", content=prev_output))

            # Call ai_providers.execute()
            response = await ai_execute(
                provider=provider,
                model=model,
                messages=messages,
                api_key=plaintext_key,
            )

        except QuotaExhaustedError:
            # 9. On QuotaExhaustedError
            await release_lock(api_key_id_str)
            async with async_session_factory() as db2:
                exec2 = await db2.get(TaskExecution, task_execution_id)
                key2 = await db2.get(APIKey, api_key_id)
                if key2:
                    key2.status = APIKeyStatus.exhausted
                if exec2:
                    exec2.status = TaskExecutionStatus.paused_exhausted
                await db2.commit()
            await notify_token_exhausted(user_id, api_key_id)
            return

        except ProviderError as exc:
            # 10. On ProviderError
            await release_lock(api_key_id_str)
            async with async_session_factory() as db2:
                exec2 = await db2.get(TaskExecution, task_execution_id)
                if exec2:
                    exec2.status = TaskExecutionStatus.failed
                await db2.commit()
            await notify_task_failed(user_id, task_execution_id, reason=str(exc))
            return

        except Exception:
            # Unexpected error — release lock and re-raise so main loop can log it
            await release_lock(api_key_id_str)
            raise

        # 11. On success — lock still held, release after storing results
        response_dict = {
            "content": response.content,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "total_tokens": response.total_tokens,
        }

        # Store Conversation record
        conversation = Conversation(
            prompt_version_id=prompt_version_id,
            provider=provider,
            model=model,
            api_key_id=api_key_id,
            full_message_log={
                "messages": [
                    {"role": m.role, "content": m.content} for m in messages
                ],
                "response": response_dict,
            },
            token_usage={
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "total_tokens": response.total_tokens,
            },
        )
        db.add(conversation)

        # Update step_outputs and advance step index
        new_step_outputs = dict(step_outputs)
        new_step_outputs[str(step_index)] = response_dict
        execution.step_outputs = new_step_outputs
        execution.current_step_index = step_index + 1
        execution.last_prompt_version_id = prompt_version_id

        # Release lock BEFORE queueing next job or marking completed
        await release_lock(api_key_id_str)

        next_step_index = step_index + 1
        if next_step_index < total_steps:
            # More steps remain — enqueue next job
            await enqueue_job(ExecuteTaskStepJob(
                task_execution_id=task_execution_id,
                step_index=next_step_index,
                api_key_id=api_key_id,
            ))
        else:
            # All steps complete
            execution.status = TaskExecutionStatus.completed
            await db.commit()
            await notify_task_completed(user_id, task_execution_id)
            return

        await db.commit()
