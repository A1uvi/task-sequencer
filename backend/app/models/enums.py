from enum import Enum


class VisibilityType(str, Enum):
    private = "private"
    team = "team"
    public = "public"


class APIKeyOwnerType(str, Enum):
    user = "user"
    team = "team"


class APIKeyStatus(str, Enum):
    active = "active"
    exhausted = "exhausted"
    revoked = "revoked"


class TaskExecutionStatus(str, Enum):
    queued = "queued"
    running = "running"
    paused_exhausted = "paused_exhausted"
    completed = "completed"
    failed = "failed"
