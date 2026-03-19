import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class PromptVersionBase(BaseModel):
    prompt_id: uuid.UUID
    content: str
    usage_notes: Optional[str] = None
    variables: dict[str, Any] = {}
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    meta_notes: Optional[str] = None
    tags: list[str] = []
    version_number: int


class PromptVersionCreate(PromptVersionBase):
    pass


class PromptVersionUpdate(BaseModel):
    # PromptVersion is immutable — updates not supported, included for completeness
    content: Optional[str] = None
    usage_notes: Optional[str] = None
    variables: Optional[dict[str, Any]] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    meta_notes: Optional[str] = None
    tags: Optional[list[str]] = None


class PromptVersionRead(PromptVersionBase):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
