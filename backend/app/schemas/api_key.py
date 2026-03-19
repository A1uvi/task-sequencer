import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import APIKeyOwnerType, APIKeyStatus


class APIKeyBase(BaseModel):
    provider: str
    owner_type: APIKeyOwnerType
    owner_id: uuid.UUID
    shared_with_users: list[uuid.UUID] = []
    shared_with_teams: list[uuid.UUID] = []
    status: APIKeyStatus = APIKeyStatus.active


class APIKeyCreate(APIKeyBase):
    # Accept the raw key on creation; service layer encrypts it
    key: str


class APIKeyUpdate(BaseModel):
    provider: Optional[str] = None
    shared_with_users: Optional[list[uuid.UUID]] = None
    shared_with_teams: Optional[list[uuid.UUID]] = None
    status: Optional[APIKeyStatus] = None


class APIKeyRead(APIKeyBase):
    id: uuid.UUID
    # Never expose encrypted_key — show only last 4 chars as masked_key
    masked_key: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_mask(cls, obj) -> "APIKeyRead":
        """Build a Read schema, masking the encrypted_key to last 4 chars."""
        data = {
            "id": obj.id,
            "provider": obj.provider,
            "owner_type": obj.owner_type,
            "owner_id": obj.owner_id,
            "shared_with_users": obj.shared_with_users,
            "shared_with_teams": obj.shared_with_teams,
            "status": obj.status,
            "masked_key": obj.encrypted_key[-4:] if obj.encrypted_key else "****",
            "created_at": obj.created_at,
        }
        return cls(**data)
