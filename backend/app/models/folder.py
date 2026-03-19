import uuid

from sqlalchemy import Enum as SAEnum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import VisibilityType


class Folder(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "folders"

    name: Mapped[str] = mapped_column(String, nullable=False)
    visibility_type: Mapped[VisibilityType] = mapped_column(
        SAEnum(VisibilityType, name="visibilitytype"),
        nullable=False,
    )
    team_ids: Mapped[list] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        default=list,
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
