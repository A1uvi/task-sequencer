import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import TaskExecutionStatus


class TaskExecutionBase(BaseModel):
    task_version_id: uuid.UUID
    api_key_id: uuid.UUID
    status: TaskExecutionStatus = TaskExecutionStatus.queued
    current_step_index: int = 0
    last_prompt_version_id: Optional[uuid.UUID] = None
    step_outputs: dict[str, Any] = {}


class TaskExecutionCreate(TaskExecutionBase):
    pass


class TaskExecutionUpdate(BaseModel):
    status: Optional[TaskExecutionStatus] = None
    current_step_index: Optional[int] = None
    last_prompt_version_id: Optional[uuid.UUID] = None
    step_outputs: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None


class TaskExecutionRead(TaskExecutionBase):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
