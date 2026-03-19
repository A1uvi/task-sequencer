import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ConversationBase(BaseModel):
    prompt_version_id: uuid.UUID
    provider: str
    model: str
    api_key_id: uuid.UUID
    full_message_log: dict[str, Any]
    token_usage: dict[str, Any]


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    # Conversation is immutable — updates not supported, included for completeness
    full_message_log: Optional[dict[str, Any]] = None
    token_usage: Optional[dict[str, Any]] = None


class ConversationRead(ConversationBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
