"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'visibilitytype') THEN
                CREATE TYPE visibilitytype AS ENUM ('private', 'team', 'public');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'apikeyownertype') THEN
                CREATE TYPE apikeyownertype AS ENUM ('user', 'team');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'apikeystatus') THEN
                CREATE TYPE apikeystatus AS ENUM ('active', 'exhausted', 'revoked');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'taskexecutionstatus') THEN
                CREATE TYPE taskexecutionstatus AS ENUM ('queued', 'running', 'paused_exhausted', 'completed', 'failed');
            END IF;
        END $$
    """))
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR NOT NULL,
            hashed_password VARCHAR NOT NULL,
            notification_preferences JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    op.execute(sa.text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS teams (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR NOT NULL,
            created_by UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS team_members (
            team_id UUID NOT NULL REFERENCES teams(id),
            user_id UUID NOT NULL REFERENCES users(id),
            role VARCHAR NOT NULL,
            PRIMARY KEY (team_id, user_id)
        )
    """))
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS folders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR NOT NULL,
            visibility_type visibilitytype NOT NULL,
            team_ids UUID[] NOT NULL DEFAULT '{}',
            created_by UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS prompts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR NOT NULL,
            folder_id UUID REFERENCES folders(id),
            visibility_type visibilitytype NOT NULL,
            created_by UUID NOT NULL REFERENCES users(id),
            current_version_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_prompts_folder_id ON prompts (folder_id)"))
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            prompt_id UUID NOT NULL REFERENCES prompts(id),
            content TEXT NOT NULL,
            usage_notes TEXT,
            variables JSONB NOT NULL DEFAULT '{}',
            example_input TEXT,
            example_output TEXT,
            meta_notes TEXT,
            tags VARCHAR[] NOT NULL DEFAULT '{}',
            version_number INTEGER NOT NULL,
            created_by UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_prompt_versions_prompt_id ON prompt_versions (prompt_id)"))
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS conversations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            prompt_version_id UUID NOT NULL REFERENCES prompt_versions(id),
            provider VARCHAR NOT NULL,
            model VARCHAR NOT NULL,
            api_key_id UUID NOT NULL,
            full_message_log JSONB NOT NULL,
            token_usage JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            provider VARCHAR NOT NULL,
            encrypted_key VARCHAR NOT NULL,
            owner_type apikeyownertype NOT NULL,
            owner_id UUID NOT NULL,
            shared_with_users UUID[] NOT NULL DEFAULT '{}',
            shared_with_teams UUID[] NOT NULL DEFAULT '{}',
            status apikeystatus NOT NULL DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_api_keys_owner_id ON api_keys (owner_id)"))
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR NOT NULL,
            folder_id UUID REFERENCES folders(id),
            visibility_type visibilitytype NOT NULL,
            created_by UUID NOT NULL REFERENCES users(id),
            current_version_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_tasks_folder_id ON tasks (folder_id)"))
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS task_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_id UUID NOT NULL REFERENCES tasks(id),
            ordered_prompt_version_ids UUID[] NOT NULL,
            default_model VARCHAR NOT NULL,
            allow_model_override_per_step BOOLEAN NOT NULL DEFAULT false,
            version_number INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_task_versions_task_id ON task_versions (task_id)"))
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS task_executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_version_id UUID NOT NULL REFERENCES task_versions(id),
            api_key_id UUID NOT NULL,
            status taskexecutionstatus NOT NULL DEFAULT 'queued',
            current_step_index INTEGER NOT NULL DEFAULT 0,
            last_prompt_version_id UUID,
            step_outputs JSONB NOT NULL DEFAULT '{}',
            created_by UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_task_executions_status ON task_executions (status)"))


def downgrade() -> None:
    for tbl in [
        "task_executions", "task_versions", "tasks", "api_keys",
        "conversations", "prompt_versions", "prompts", "folders",
        "team_members", "teams", "users",
    ]:
        op.execute(sa.text(f"DROP TABLE IF EXISTS {tbl} CASCADE"))
    for typ in ["taskexecutionstatus", "apikeystatus", "apikeyownertype", "visibilitytype"]:
        op.execute(sa.text(f"DROP TYPE IF EXISTS {typ}"))
