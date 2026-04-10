import uuid

from sqlalchemy import Enum as SAEnum, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import TaskExecutionStatus


class TaskExecution(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "task_executions"
    __table_args__ = (
        Index("ix_task_executions_status", "status"),
    )

    task_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_versions.id"),
        nullable=False,
    )
    api_key_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[TaskExecutionStatus] = mapped_column(
        SAEnum(TaskExecutionStatus, name="taskexecutionstatus"),
        default=TaskExecutionStatus.queued,
        nullable=False,
    )
    current_step_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_prompt_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    # {step_index: response_dict}
    step_outputs: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
