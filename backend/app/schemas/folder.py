import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import VisibilityType


class FolderBase(BaseModel):
    name: str
    visibility_type: VisibilityType
    team_ids: list[uuid.UUID] = []


class FolderCreate(FolderBase):
    pass


class FolderUpdate(BaseModel):
    name: Optional[str] = None
    visibility_type: Optional[VisibilityType] = None
    team_ids: Optional[list[uuid.UUID]] = None


class FolderRead(FolderBase):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
