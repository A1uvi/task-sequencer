import os
import uuid
import logging

from jinja2 import Environment, FileSystemLoader

from app.core.database import async_session_factory
from app.models import User, APIKey
from app.services.notification_prefs import should_notify
from app.services.email import send_email

logger = logging.getLogger(__name__)


def _render_template(template_name: str, **context) -> str:
    """Render a Jinja2 email template from the templates/emails directory."""
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "emails")
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template(template_name)
    return template.render(**context)


async def notify_token_exhausted(user_id: uuid.UUID, api_key_id: uuid.UUID) -> None:
    """Send token exhausted notification if user preferences allow it."""
    try:
        async with async_session_factory() as db:
            user = await db.get(User, user_id)
            if not user:
                return
            if not should_notify(user, "token_exhausted"):
                return
            api_key = await db.get(APIKey, api_key_id)
            last4 = api_key.encrypted_key[-4:] if api_key else "????"
            html = _render_template("token_exhausted.html", api_key_last4=last4)
            logger.info(f"Sending token_exhausted notification to user {user_id}")
            await send_email(
                to=user.email,
                subject="API Key Token Limit Reached",
                html_body=html,
            )
    except Exception as e:
        logger.error(f"notify_token_exhausted failed for user {user_id}: {e}")


async def notify_tokens_refilled(user_id: uuid.UUID, api_key_id: uuid.UUID) -> None:
    """Send token refilled notification if user preferences allow it."""
    try:
        async with async_session_factory() as db:
            user = await db.get(User, user_id)
            if not user:
                return
            if not should_notify(user, "tokens_refilled"):
                return
            api_key = await db.get(APIKey, api_key_id)
            last4 = api_key.encrypted_key[-4:] if api_key else "????"
            html = _render_template("tokens_refilled.html", api_key_last4=last4)
            logger.info(f"Sending tokens_refilled notification to user {user_id}")
            await send_email(
                to=user.email,
                subject="API Tokens Refilled",
                html_body=html,
            )
    except Exception as e:
        logger.error(f"notify_tokens_refilled failed for user {user_id}: {e}")


async def notify_task_completed(user_id: uuid.UUID, task_execution_id: uuid.UUID) -> None:
    """Send task completed notification if user preferences allow it."""
    try:
        async with async_session_factory() as db:
            user = await db.get(User, user_id)
            if not user:
                return
            if not should_notify(user, "task_completed"):
                return
            html = _render_template(
                "task_completed.html",
                task_execution_id=str(task_execution_id),
            )
            logger.info(f"Sending task_completed notification to user {user_id}")
            await send_email(
                to=user.email,
                subject="Task Completed",
                html_body=html,
            )
    except Exception as e:
        logger.error(f"notify_task_completed failed for user {user_id}: {e}")


async def notify_task_failed(
    user_id: uuid.UUID, task_execution_id: uuid.UUID, reason: str
) -> None:
    """Send task failed notification if user preferences allow it."""
    try:
        async with async_session_factory() as db:
            user = await db.get(User, user_id)
            if not user:
                return
            if not should_notify(user, "task_failed"):
                return
            html = _render_template(
                "task_failed.html",
                task_execution_id=str(task_execution_id),
                reason=reason,
            )
            logger.info(f"Sending task_failed notification to user {user_id}")
            await send_email(
                to=user.email,
                subject="Task Failed",
                html_body=html,
            )
    except Exception as e:
        logger.error(f"notify_task_failed failed for user {user_id}: {e}")
