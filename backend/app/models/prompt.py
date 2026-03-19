import uuid

from sqlalchemy import Enum as SAEnum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import VisibilityType


class Prompt(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "prompts"
    __table_args__ = (
        Index("ix_prompts_folder_id", "folder_id"),
    )

    title: Mapped[str] = mapped_column(String, nullable=False)
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("folders.id"),
        nullable=True,
    )
    visibility_type: Mapped[VisibilityType] = mapped_column(
        SAEnum(VisibilityType, name="visibilitytype"),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    # Not a FK to avoid circular dependency with PromptVersion
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
