import json
import logging
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Audit logs table name — mirrors the migration 0002 definition
_AUDIT_TABLE = "audit_logs"


async def log_event(
    db: AsyncSession,
    user_id: uuid.UUID,
    event_type: str,
    resource_id: uuid.UUID,
    metadata: dict | None = None,
) -> None:
    """Write an audit log entry to audit_logs table.

    Never raises — all exceptions are caught and logged as warnings so that
    audit failures never break the main request flow.
    """
    try:
        await db.execute(
            sa.text(
                f"""
                INSERT INTO {_AUDIT_TABLE}
                    (user_id, event_type, resource_id, metadata, created_at)
                VALUES
                    (:user_id, :event_type, :resource_id, :metadata::jsonb, :created_at)
                """
            ),
            {
                "user_id": str(user_id),
                "event_type": event_type,
                "resource_id": str(resource_id),
                "metadata": json.dumps(metadata or {}),
                "created_at": datetime.now(timezone.utc),
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "audit log failed: event_type=%s user_id=%s resource_id=%s error=%r",
            event_type,
            user_id,
            resource_id,
            exc,
        )
