"""Email sender with a stdout fallback for local dev.

Behavior:
- If SMTP_HOST is set (not placeholder), send via aiosmtplib. Raises on failure.
- If SMTP_HOST is empty / example, print to stdout.
"""

from __future__ import annotations

import logging
from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


def _is_smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_HOST != "smtp.example.com")


async def send_email(
    *,
    to: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
) -> None:
    """Send an email. Raises on real SMTP failure. Falls back to stdout when not configured."""
    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    if not _is_smtp_configured():
        _print_to_stdout(to, subject, body_text, body_html)
        return

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER or None,
        password=settings.SMTP_PASSWORD or None,
        start_tls=settings.SMTP_PORT == 587,
        use_tls=settings.SMTP_PORT == 465,
    )
    logger.info("Email sent to %s: %s", to, subject)


def _print_to_stdout(to: str, subject: str, body_text: str, body_html: str | None) -> None:
    banner = "=" * 60
    logger.info("\n%s\n[DEV EMAIL] To: %s\n[DEV EMAIL] Subject: %s\n%s\n%s\n%s",
                banner, to, subject, banner, body_text, banner)
    if body_html:
        logger.info("[DEV EMAIL HTML]:\n%s\n%s", body_html, banner)
