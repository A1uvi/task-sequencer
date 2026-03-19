import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TaskVersionBase(BaseModel):
    task_id: uuid.UUID
    ordered_prompt_version_ids: list[uuid.UUID]
    default_model: str
    allow_model_override_per_step: bool = False
    version_number: int


class TaskVersionCreate(TaskVersionBase):
    pass


class TaskVersionUpdate(BaseModel):
    # TaskVersion is immutable — updates not supported, included for completeness
    ordered_prompt_version_ids: Optional[list[uuid.UUID]] = None
    default_model: Optional[str] = None
    allow_model_override_per_step: Optional[bool] = None


class TaskVersionRead(TaskVersionBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
