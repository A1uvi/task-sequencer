import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class PromptVersion(UUIDMixin, Base):
    """Immutable record — no updated_at."""

    __tablename__ = "prompt_versions"
    __table_args__ = (
        Index("ix_prompt_versions_prompt_id", "prompt_id"),
    )

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    usage_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    variables: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    example_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
