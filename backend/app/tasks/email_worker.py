"""Background email worker — polls email_outbox and sends via SMTP.

Integrated into FastAPI via lifespan, no separate process needed.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import settings
from app.core.email import send_email
from app.db.session import AsyncSessionLocal
from app.modules.notifications.models import EmailOutbox

logger = logging.getLogger("labinherit.email_worker")


async def process_batch() -> int:
    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        result = await db.execute(
            select(EmailOutbox)
            .where(
                EmailOutbox.status == "queued",
                EmailOutbox.next_attempt_at <= now,
            )
            .order_by(EmailOutbox.next_attempt_at.asc())
            .limit(settings.EMAIL_WORKER_BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )
        entries = result.scalars().all()

        if not entries:
            return 0

        for entry in entries:
            try:
                await send_email(
                    to=entry.to_email,
                    subject=entry.subject,
                    body_text=entry.body_text,
                    body_html=entry.body_html,
                )
                entry.status = "sent"
                logger.info("Email sent: %s → %s", entry.subject, entry.to_email)
            except Exception as exc:
                entry.retry_count += 1
                entry.last_error = str(exc)[:500]
                if entry.retry_count >= settings.EMAIL_WORKER_MAX_RETRIES:
                    entry.status = "failed"
                    logger.error(
                        "Email FAILED after %d retries: %s → %s: %s",
                        entry.retry_count, entry.subject, entry.to_email, exc,
                    )
                else:
                    backoff = 2 ** entry.retry_count
                    entry.next_attempt_at = now + timedelta(minutes=backoff)
                    logger.warning(
                        "Email retry #%d (next in %d min): %s → %s",
                        entry.retry_count, backoff, entry.subject, entry.to_email,
                    )

        await db.commit()
        return len(entries)


async def run_worker(stop_event: asyncio.Event) -> None:
    interval = settings.EMAIL_WORKER_POLL_INTERVAL
    logger.info(
        "Email worker started (poll=%ds, batch=%d, max_retries=%d)",
        interval,
        settings.EMAIL_WORKER_BATCH_SIZE,
        settings.EMAIL_WORKER_MAX_RETRIES,
    )
    while not stop_event.is_set():
        try:
            count = await process_batch()
            if count:
                logger.info("Processed %d email(s)", count)
        except Exception as exc:
            logger.exception("Email worker error: %s", exc)

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
            break
        except asyncio.TimeoutError:
            pass

    logger.info("Email worker stopped.")
