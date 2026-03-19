from app.models import User

NOTIFICATION_KEYS = {
    "token_exhausted": "notify_token_exhausted",
    "tokens_refilled": "notify_tokens_refilled",
    "task_completed": "notify_task_completed",
    "task_failed": "notify_task_failed",
}


def should_notify(user: User, event_type: str) -> bool:
    """Check user.notification_preferences for the given event_type.
    Returns True (default) when key is absent from JSONB."""
    prefs = user.notification_preferences or {}
    key = NOTIFICATION_KEYS.get(event_type, event_type)
    return bool(prefs.get(key, True))  # default True when absent
