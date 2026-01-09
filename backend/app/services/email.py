"""
Simple email helpers used by authentication workflows.
"""
import logging
import ssl
import smtplib
from email.message import EmailMessage
from typing import Optional

from ..config import settings

logger = logging.getLogger(__name__)


def _build_from_header() -> str:
    return f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"


def send_email(
    recipient: str,
    subject: str,
    text_body: str,
    html_body: Optional[str] = None
) -> None:
    """
    Attempt to send an email via SMTP when credentials are configured.
    Falls back to logging the content so developers can copy tokens manually.
    """
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = _build_from_header()
    message["To"] = recipient
    message.set_content(text_body)

    if html_body:
        message.add_alternative(html_body, subtype="html")

    logger.debug(f"Email sending attempt: SMTP_HOST={settings.SMTP_HOST}, SMTP_USERNAME={settings.SMTP_USERNAME}, has_password={bool(settings.SMTP_PASSWORD)}")

    if settings.SMTP_HOST and settings.SMTP_PASSWORD:
        try:
            logger.info(f"Attempting to send email to {recipient} via SMTP host {settings.SMTP_HOST}:{settings.SMTP_PORT}")
            context = ssl.create_default_context()
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT) as smtp:
                if settings.SMTP_USE_TLS:
                    logger.debug("Starting TLS...")
                    smtp.starttls(context=context)
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    logger.debug(f"Logging in as {settings.SMTP_USERNAME}...")
                    smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                logger.debug(f"Sending message to {recipient}...")
                smtp.send_message(message)
            logger.info(f"Successfully sent email to {recipient}")
            return
        except Exception as exc:  # pragma: no cover - best-effort logging
            logger.error(f"Failed to send email to {recipient}: {type(exc).__name__}: {exc}", exc_info=True)
            raise

    logger.warning(
        f"SMTP not fully configured (SMTP_HOST={settings.SMTP_HOST}, SMTP_PASSWORD set={bool(settings.SMTP_PASSWORD)}). Email would not be sent.\nTo: {recipient}\nSubject: {subject}\n\nBody:\n{text_body}"
    )


def send_verification_email(recipient: str, token: str, full_name: Optional[str] = None) -> None:
    """Send a verification email containing the token and basic instructions."""
    display_name = full_name or "candidate"
    verification_url = f"{settings.APP_URL}{settings.EMAIL_VERIFICATION_PATH}"
    subject = "Verify your HireSight account"

    text_body = (
        f"Hi {display_name},\n\n"
        "Welcome to HireSight! Please verify your email address before signing in.\n\n"
        f"Use the following verification token:\n\n  {token}\n\n"
        f"You can submit the token via POST {verification_url} (JSON body: {{\"token\": \"<token>\"}}).\n\n"
        "If you didn’t sign up for HireSight, no action is required.\n\n"
        "Thanks,\nHireSight Team"
    )

    html_body = (
        f"<p>Hi {display_name},</p>"
        "<p>Welcome to <strong>HireSight</strong>! Please verify your email address before signing in.</p>"
        f'<p><strong>Your verification token:</strong><br><code>{token}</code></p>'
        f"<p>Send it to <code>{verification_url}</code> using a POST request with <code>{{\"token\": \"<token>\"}}</code>.</p>"
        "<p>If you didn’t request this, you can ignore this email.</p>"
        "<p>Thanks,<br><strong>HireSight Team</strong></p>"
    )

    send_email(recipient, subject, text_body, html_body)


def send_password_reset_email(recipient: str, token: str, full_name: Optional[str] = None) -> None:
    """Send a password reset email containing the token and next steps."""
    display_name = full_name or "candidate"
    reset_url = f"{settings.APP_URL}/auth/reset-password"
    subject = "HireSight password reset request"

    text_body = (
        f"Hi {display_name},\n\n"
        "We received a request to reset your HireSight password. "
        "If you didn’t ask for this, you can safely ignore this email.\n\n"
        f"Use the following token to reset your password (expires in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hour(s)):\n\n"
        f"  {token}\n\n"
        f"Send it along with your new password to {reset_url} (JSON body: "
        "{{\"token\": \"<token>\", \"new_password\": \"YourStrongPassword\"}}).\n\n"
        "Thank you,\nHireSight Team"
    )

    html_body = (
        f"<p>Hi {display_name},</p>"
        "<p>We received a request to reset your HireSight password. "
        "If you didn’t request this, you can ignore this message.</p>"
        f"<p><strong>Your reset token:</strong><br><code>{token}</code></p>"
        f'<p>POST it with your new password to <code>{reset_url}</code> using JSON like '
        '<code>{"token": "<token>", "new_password": "YourStrongPassword"}</code>.</p>'
        "<p>Token expires in "
        f"{settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hour(s).</p>"
        "<p>Thanks,<br><strong>HireSight</strong></p>"
    )

    send_email(recipient, subject, text_body, html_body)
