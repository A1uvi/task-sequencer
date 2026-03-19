import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import TaskExecution, TaskVersion, User
from app.models.enums import TaskExecutionStatus
from app.schemas.task_execution import TaskExecutionRead
from app.services.audit import log_event
from app.services.permissions import user_can_use_api_key
from app.worker.jobs import ExecuteTaskStepJob
from app.worker.queue import enqueue_job

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]


class TaskExecutionCreateRequest(BaseModel):
    task_version_id: uuid.UUID
    api_key_id: uuid.UUID


@router.post("", response_model=TaskExecutionRead, status_code=status.HTTP_201_CREATED)
async def initiate_task_execution(
    body: TaskExecutionCreateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> TaskExecutionRead:
    """Initiate a task execution. Checks permissions, creates a queued record,
    enqueues the worker job, and logs an audit event.
    """
    # Verify the task version exists
    tv_result = await db.execute(
        select(TaskVersion).where(TaskVersion.id == body.task_version_id)
    )
    task_version = tv_result.scalar_one_or_none()
    if task_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="TaskVersion not found"
        )

    # Check API key permission
    if not await user_can_use_api_key(current_user.id, body.api_key_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to use this API key",
        )

    execution = TaskExecution(
        task_version_id=body.task_version_id,
        api_key_id=body.api_key_id,
        status=TaskExecutionStatus.queued,
        current_step_index=0,
        step_outputs={},
        created_by=current_user.id,
    )
    db.add(execution)
    await db.flush()

    # Enqueue the job for the worker process
    job = ExecuteTaskStepJob(
        task_execution_id=execution.id,
        step_index=0,
        api_key_id=body.api_key_id,
    )
    await enqueue_job(job)

    await log_event(
        db=db,
        user_id=current_user.id,
        event_type="task_execution.started",
        resource_id=execution.id,
        metadata={
            "task_version_id": str(body.task_version_id),
            "api_key_id": str(body.api_key_id),
        },
    )

    return TaskExecutionRead.model_validate(execution)


@router.get("", response_model=list[TaskExecutionRead])
async def list_task_executions(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[TaskExecutionRead]:
    """List task executions created by the current user."""
    result = await db.execute(
        select(TaskExecution)
        .where(TaskExecution.created_by == current_user.id)
        .order_by(TaskExecution.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    executions = result.scalars().all()
    return [TaskExecutionRead.model_validate(e) for e in executions]


@router.get("/{execution_id}", response_model=TaskExecutionRead)
async def get_task_execution(
    execution_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> TaskExecutionRead:
    """Poll the status of a task execution. Only accessible by creator."""
    result = await db.execute(
        select(TaskExecution).where(TaskExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="TaskExecution not found"
        )

    if execution.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return TaskExecutionRead.model_validate(execution)
