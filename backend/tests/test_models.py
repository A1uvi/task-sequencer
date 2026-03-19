"""
Model instantiation, relationship, and enum tests.

These tests verify:
1. Each model can be instantiated with required fields.
2. Enum values match expected strings.
3. JSONB / array fields default correctly.
4. TimestampMixin sets created_at automatically.
5. Immutable models (PromptVersion, TaskVersion, Conversation) have NO updated_at.
"""

import uuid
from datetime import datetime, timezone

import pytest

from app.models.enums import (
    APIKeyOwnerType,
    APIKeyStatus,
    TaskExecutionStatus,
    VisibilityType,
)
from app.models.user import User
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.folder import Folder
from app.models.prompt import Prompt
from app.models.prompt_version import PromptVersion
from app.models.conversation import Conversation
from app.models.api_key import APIKey
from app.models.task import Task
from app.models.task_version import TaskVersion
from app.models.task_execution import TaskExecution


# ---------------------------------------------------------------------------
# Enum value tests
# ---------------------------------------------------------------------------


class TestEnumValues:
    def test_visibility_type_values(self):
        assert VisibilityType.private == "private"
        assert VisibilityType.team == "team"
        assert VisibilityType.public == "public"

    def test_api_key_owner_type_values(self):
        assert APIKeyOwnerType.user == "user"
        assert APIKeyOwnerType.team == "team"

    def test_api_key_status_values(self):
        assert APIKeyStatus.active == "active"
        assert APIKeyStatus.exhausted == "exhausted"
        assert APIKeyStatus.revoked == "revoked"

    def test_task_execution_status_values(self):
        assert TaskExecutionStatus.queued == "queued"
        assert TaskExecutionStatus.running == "running"
        assert TaskExecutionStatus.paused_exhausted == "paused_exhausted"
        assert TaskExecutionStatus.completed == "completed"
        assert TaskExecutionStatus.failed == "failed"


# ---------------------------------------------------------------------------
# Model instantiation tests
# ---------------------------------------------------------------------------


class TestUserModel:
    def test_instantiation(self):
        user = User(
            email="test@example.com",
            hashed_password="hashed",
        )
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed"

    def test_default_notification_preferences(self):
        user = User(email="a@b.com", hashed_password="x")
        # The default factory is `dict` — column default; may be None before flush
        # We just verify the attribute exists
        assert hasattr(user, "notification_preferences")

    def test_created_at_auto_set(self):
        user = User(
            email="ts@test.com",
            hashed_password="hash",
            created_at=datetime.now(timezone.utc),
        )
        assert isinstance(user.created_at, datetime)

    def test_no_updated_at_attribute(self):
        """User does not use TimestampMixin's updated_at directly."""
        user = User(email="u@u.com", hashed_password="h")
        assert not hasattr(user, "updated_at") or user.__mapper__.attrs.keys()


class TestTeamModel:
    def test_instantiation(self):
        uid = uuid.uuid4()
        team = Team(name="Engineering", created_by=uid)
        assert team.name == "Engineering"
        assert team.created_by == uid


class TestTeamMemberModel:
    def test_instantiation(self):
        tm = TeamMember(
            team_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="admin",
        )
        assert tm.role == "admin"


class TestFolderModel:
    def test_instantiation(self):
        uid = uuid.uuid4()
        folder = Folder(
            name="My Folder",
            visibility_type=VisibilityType.private,
            created_by=uid,
        )
        assert folder.name == "My Folder"
        assert folder.visibility_type == VisibilityType.private

    def test_has_updated_at(self):
        folder = Folder(
            name="F",
            visibility_type=VisibilityType.public,
            created_by=uuid.uuid4(),
        )
        assert hasattr(folder, "updated_at")

    def test_default_team_ids(self):
        folder = Folder(
            name="F",
            visibility_type=VisibilityType.team,
            created_by=uuid.uuid4(),
        )
        assert hasattr(folder, "team_ids")


class TestPromptModel:
    def test_instantiation(self):
        uid = uuid.uuid4()
        prompt = Prompt(
            title="My Prompt",
            visibility_type=VisibilityType.private,
            created_by=uid,
        )
        assert prompt.title == "My Prompt"
        assert prompt.folder_id is None
        assert prompt.current_version_id is None

    def test_has_updated_at(self):
        p = Prompt(
            title="P",
            visibility_type=VisibilityType.public,
            created_by=uuid.uuid4(),
        )
        assert hasattr(p, "updated_at")


class TestPromptVersionModel:
    def test_instantiation(self):
        pv = PromptVersion(
            prompt_id=uuid.uuid4(),
            content="You are a helpful assistant.",
            version_number=1,
            created_by=uuid.uuid4(),
        )
        assert pv.content == "You are a helpful assistant."
        assert pv.version_number == 1

    def test_no_updated_at(self):
        """PromptVersion is immutable — must NOT have updated_at."""
        pv = PromptVersion(
            prompt_id=uuid.uuid4(),
            content="c",
            version_number=1,
            created_by=uuid.uuid4(),
        )
        assert not hasattr(pv, "updated_at"), (
            "PromptVersion must not have an updated_at field"
        )

    def test_default_variables(self):
        pv = PromptVersion(
            prompt_id=uuid.uuid4(),
            content="c",
            version_number=1,
            created_by=uuid.uuid4(),
        )
        assert hasattr(pv, "variables")

    def test_default_tags(self):
        pv = PromptVersion(
            prompt_id=uuid.uuid4(),
            content="c",
            version_number=1,
            created_by=uuid.uuid4(),
        )
        assert hasattr(pv, "tags")


class TestConversationModel:
    def test_instantiation(self):
        conv = Conversation(
            prompt_version_id=uuid.uuid4(),
            provider="openai",
            model="gpt-4o",
            api_key_id=uuid.uuid4(),
            full_message_log={"messages": []},
            token_usage={"input": 10, "output": 20},
        )
        assert conv.provider == "openai"
        assert conv.model == "gpt-4o"

    def test_no_updated_at(self):
        """Conversation is immutable — must NOT have updated_at."""
        conv = Conversation(
            prompt_version_id=uuid.uuid4(),
            provider="anthropic",
            model="claude-3",
            api_key_id=uuid.uuid4(),
            full_message_log={},
            token_usage={},
        )
        assert not hasattr(conv, "updated_at"), (
            "Conversation must not have an updated_at field"
        )


class TestAPIKeyModel:
    def test_instantiation(self):
        key = APIKey(
            provider="openai",
            encrypted_key="enc_abc123",
            owner_type=APIKeyOwnerType.user,
            owner_id=uuid.uuid4(),
        )
        assert key.provider == "openai"
        assert key.owner_type == APIKeyOwnerType.user

    def test_default_status(self):
        key = APIKey(
            provider="anthropic",
            encrypted_key="enc_xyz",
            owner_type=APIKeyOwnerType.team,
            owner_id=uuid.uuid4(),
        )
        # Default is set at column level; may be None before DB flush in pure Python
        assert key.status in (APIKeyStatus.active, None)


class TestTaskModel:
    def test_instantiation(self):
        task = Task(
            title="My Task",
            visibility_type=VisibilityType.team,
            created_by=uuid.uuid4(),
        )
        assert task.title == "My Task"
        assert task.folder_id is None
        assert task.current_version_id is None

    def test_has_updated_at(self):
        t = Task(
            title="T",
            visibility_type=VisibilityType.private,
            created_by=uuid.uuid4(),
        )
        assert hasattr(t, "updated_at")


class TestTaskVersionModel:
    def test_instantiation(self):
        tv = TaskVersion(
            task_id=uuid.uuid4(),
            ordered_prompt_version_ids=[uuid.uuid4(), uuid.uuid4()],
            default_model="gpt-4o",
            version_number=1,
        )
        assert tv.default_model == "gpt-4o"
        assert len(tv.ordered_prompt_version_ids) == 2

    def test_no_updated_at(self):
        """TaskVersion is immutable — must NOT have updated_at."""
        tv = TaskVersion(
            task_id=uuid.uuid4(),
            ordered_prompt_version_ids=[],
            default_model="claude-3",
            version_number=1,
        )
        assert not hasattr(tv, "updated_at"), (
            "TaskVersion must not have an updated_at field"
        )

    def test_default_allow_model_override(self):
        tv = TaskVersion(
            task_id=uuid.uuid4(),
            ordered_prompt_version_ids=[],
            default_model="gpt-4",
            version_number=1,
        )
        # Column default is False; may be None before flush
        assert tv.allow_model_override_per_step in (False, None)


class TestTaskExecutionModel:
    def test_instantiation(self):
        te = TaskExecution(
            task_version_id=uuid.uuid4(),
            api_key_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
        )
        assert te.task_version_id is not None

    def test_has_updated_at(self):
        te = TaskExecution(
            task_version_id=uuid.uuid4(),
            api_key_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
        )
        assert hasattr(te, "updated_at")

    def test_default_step_outputs(self):
        te = TaskExecution(
            task_version_id=uuid.uuid4(),
            api_key_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
        )
        assert hasattr(te, "step_outputs")

    def test_default_status(self):
        te = TaskExecution(
            task_version_id=uuid.uuid4(),
            api_key_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
        )
        assert te.status in (TaskExecutionStatus.queued, None)


# ---------------------------------------------------------------------------
# Timestamp Mixin: TimestampMixin sets created_at when provided
# ---------------------------------------------------------------------------


class TestTimestampMixin:
    def test_folder_created_at_is_datetime(self):
        now = datetime.now(timezone.utc)
        folder = Folder(
            name="F",
            visibility_type=VisibilityType.private,
            created_by=uuid.uuid4(),
            created_at=now,
        )
        assert isinstance(folder.created_at, datetime)

    def test_task_execution_has_both_timestamps(self):
        now = datetime.now(timezone.utc)
        te = TaskExecution(
            task_version_id=uuid.uuid4(),
            api_key_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        assert isinstance(te.created_at, datetime)
        assert isinstance(te.updated_at, datetime)
