import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_should_notify_default_true():
    """Returns True when key absent from prefs."""
    from app.services.notification_prefs import should_notify
    from app.models import User
    user = User(notification_preferences={})
    assert should_notify(user, "token_exhausted") is True


@pytest.mark.asyncio
async def test_should_notify_explicit_false():
    """Returns False when user has disabled this notification."""
    from app.services.notification_prefs import should_notify
    from app.models import User
    user = User(notification_preferences={"notify_token_exhausted": False})
    assert should_notify(user, "token_exhausted") is False


@pytest.mark.asyncio
async def test_should_notify_explicit_true():
    from app.services.notification_prefs import should_notify
    from app.models import User
    user = User(notification_preferences={"notify_token_exhausted": True})
    assert should_notify(user, "token_exhausted") is True


@pytest.mark.asyncio
async def test_notify_token_exhausted_skips_when_disabled():
    """No email sent when user has disabled the notification."""
    from app.services import notifications
    with patch("app.services.notifications.async_session_factory") as mock_factory:
        mock_session = AsyncMock()
        mock_user = MagicMock()
        mock_user.notification_preferences = {"notify_token_exhausted": False}
        mock_user.email = "test@example.com"
        mock_session.get = AsyncMock(return_value=mock_user)
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.notifications.send_email") as mock_send:
            await notifications.notify_token_exhausted(uuid.uuid4(), uuid.uuid4())
            mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_notify_token_exhausted_sends_when_enabled():
    """Email is sent when preferences allow it."""
    from app.services import notifications
    with patch("app.services.notifications.async_session_factory") as mock_factory:
        mock_session = AsyncMock()
        mock_user = MagicMock()
        mock_user.notification_preferences = {}
        mock_user.email = "test@example.com"
        mock_api_key = MagicMock()
        mock_api_key.encrypted_key = "encrypted_data_1234"
        mock_session.get = AsyncMock(side_effect=[mock_user, mock_api_key])
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.notifications.send_email") as mock_send:
            await notifications.notify_token_exhausted(uuid.uuid4(), uuid.uuid4())
            mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_email_send_failure_does_not_raise():
    """Email failure is caught silently — never propagates."""
    from app.services.email import send_email
    with patch("app.services.email._send_via_sendgrid", side_effect=Exception("SMTP down")):
        with patch("app.services.email._send_via_smtp", side_effect=Exception("SMTP down")):
            # Should not raise
            await send_email("test@example.com", "Test", "<p>Test</p>")


def test_template_rendering():
    """Templates render without errors and contain key content."""
    from app.services.notifications import _render_template
    html = _render_template("token_exhausted.html", api_key_last4="5678")
    assert "5678" in html
    assert "Token" in html or "token" in html.lower()


def test_task_failed_template_includes_reason():
    from app.services.notifications import _render_template
    html = _render_template("task_failed.html", task_execution_id="exec-123", reason="Provider timeout")
    assert "Provider timeout" in html
    assert "exec-123" in html
