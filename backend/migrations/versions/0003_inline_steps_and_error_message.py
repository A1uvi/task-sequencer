"""Add inline steps JSONB and error_message to task_executions

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-19 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("task_versions", "ordered_prompt_version_ids")
    op.add_column(
        "task_versions",
        sa.Column("steps", JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "task_executions",
        sa.Column("error_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("task_executions", "error_message")
    op.drop_column("task_versions", "steps")
    op.add_column(
        "task_versions",
        sa.Column(
            "ordered_prompt_version_ids",
            sa.ARRAY(sa.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
    )
