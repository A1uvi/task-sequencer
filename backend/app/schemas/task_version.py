import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class TaskVersionBase(BaseModel):
    task_id: uuid.UUID
    steps: list[dict[str, Any]]
    default_model: str
    allow_model_override_per_step: bool = False
    version_number: int


class TaskVersionCreate(TaskVersionBase):
    pass


class TaskVersionUpdate(BaseModel):
    # TaskVersion is immutable — updates not supported, included for completeness
    steps: Optional[list[dict[str, Any]]] = None
    default_model: Optional[str] = None
    allow_model_override_per_step: Optional[bool] = None


class TaskVersionRead(TaskVersionBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
