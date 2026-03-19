import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class TaskVersion(UUIDMixin, Base):
    """Immutable record — no updated_at."""

    __tablename__ = "task_versions"
    __table_args__ = (
        Index("ix_task_versions_task_id", "task_id"),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id"),
        nullable=False,
    )
    ordered_prompt_version_ids: Mapped[list] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        nullable=False,
    )
    default_model: Mapped[str] = mapped_column(nullable=False)
    allow_model_override_per_step: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
