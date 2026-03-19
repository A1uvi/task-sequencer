import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, html_body: str) -> None:
    """Send transactional email. Uses SendGrid if configured, falls back to SMTP.
    NEVER raises exceptions — all errors are caught and logged."""
    try:
        if settings.email_provider == "sendgrid" and settings.sendgrid_api_key:
            await _send_via_sendgrid(to, subject, html_body)
        else:
            await _send_via_smtp(to, subject, html_body)
        logger.info(f"Email sent to {to}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        # Never re-raise


async def _send_via_sendgrid(to: str, subject: str, html_body: str) -> None:
    """Send via SendGrid API."""
    import sendgrid
    from sendgrid.helpers.mail import Mail

    sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
    message = Mail(
        from_email=settings.from_email,
        to_emails=to,
        subject=subject,
        html_content=html_body,
    )
    response = sg.client.mail.send.post(request_body=message.get())
    if response.status_code >= 400:
        raise Exception(f"SendGrid API error: {response.status_code} {response.body}")


async def _send_via_smtp(to: str, subject: str, html_body: str) -> None:
    """Send via SMTP using aiosmtplib."""
    import aiosmtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.from_email
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_pass,
        start_tls=True,
    )
