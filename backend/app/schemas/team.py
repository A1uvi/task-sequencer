import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TeamBase(BaseModel):
    name: str


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None


class TeamRead(TeamBase):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamMemberBase(BaseModel):
    team_id: uuid.UUID
    user_id: uuid.UUID
    role: str


class TeamMemberCreate(TeamMemberBase):
    pass


class TeamMemberUpdate(BaseModel):
    role: Optional[str] = None


class TeamMemberRead(TeamMemberBase):
    model_config = ConfigDict(from_attributes=True)
