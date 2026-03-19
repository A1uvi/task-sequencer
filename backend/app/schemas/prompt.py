import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import VisibilityType


class PromptBase(BaseModel):
    title: str
    folder_id: Optional[uuid.UUID] = None
    visibility_type: VisibilityType


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    title: Optional[str] = None
    folder_id: Optional[uuid.UUID] = None
    visibility_type: Optional[VisibilityType] = None
    current_version_id: Optional[uuid.UUID] = None


class PromptRead(PromptBase):
    id: uuid.UUID
    created_by: uuid.UUID
    current_version_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
