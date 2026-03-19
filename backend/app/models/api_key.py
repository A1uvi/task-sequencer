import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, Index, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin
from app.models.enums import APIKeyOwnerType, APIKeyStatus


class APIKey(UUIDMixin, Base):
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("ix_api_keys_owner_id", "owner_id"),
    )

    provider: Mapped[str] = mapped_column(String, nullable=False)
    # Encryption is a service layer concern — stored as plain String here
    encrypted_key: Mapped[str] = mapped_column(String, nullable=False)
    owner_type: Mapped[APIKeyOwnerType] = mapped_column(
        SAEnum(APIKeyOwnerType, name="apikeyownertype"),
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    shared_with_users: Mapped[list] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        default=list,
        nullable=False,
    )
    shared_with_teams: Mapped[list] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        default=list,
        nullable=False,
    )
    status: Mapped[APIKeyStatus] = mapped_column(
        SAEnum(APIKeyStatus, name="apikeystatus"),
        default=APIKeyStatus.active,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
