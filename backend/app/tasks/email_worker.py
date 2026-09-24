"""Background email worker — polls email_outbox and sends via SMTP.

Can run in two modes:
1. Integrated into FastAPI via lifespan (automatic background task)
2. Standalone process: python -m app.tasks.email_worker
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

# Minimal imports for the worker
from app.core.config import settings
from app.core.email import send_email
from app.db.session import AsyncSessionLocal

# Import models in the same order as alembic to avoid dependency issues
from app.db import Base  # noqa: F401 - ensures metadata is initialized
from app.modules.users.models import User, UserProfile  # noqa: F401 - needed for relationships
from app.modules.invites.models import Invite  # noqa: F401 - needed for User relationship
from app.modules.audit.models import AuditQueue  # noqa: F401 - needed for User relationship
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


def main() -> None:
    """Standalone entry point for running the email worker as a separate process."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="LabInherit Email Worker - Background email sender",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.tasks.email_worker
  python -m app.tasks.email_worker --interval 10 --batch-size 20
  python -m app.tasks.email_worker --log-level DEBUG
        """,
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=settings.EMAIL_WORKER_POLL_INTERVAL,
        help=f"Polling interval in seconds (default: {settings.EMAIL_WORKER_POLL_INTERVAL})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=settings.EMAIL_WORKER_BATCH_SIZE,
        help=f"Batch size for processing emails (default: {settings.EMAIL_WORKER_BATCH_SIZE})",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    
    args = parser.parse_args()
    
    # Override settings with CLI args
    settings.EMAIL_WORKER_POLL_INTERVAL = args.interval
    settings.EMAIL_WORKER_BATCH_SIZE = args.batch_size
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    
    logger.info("=" * 60)
    logger.info("LabInherit Email Worker v1.0")
    logger.info("=" * 60)
    logger.info("Starting in standalone mode...")
    logger.info("Database: %s", settings.database_url.split("@")[-1])  # Hide password
    logger.info("SMTP configured: %s", "yes" if settings.SMTP_HOST != "smtp.example.com" else "no (stdout mode)")
    logger.info("Poll interval: %d seconds", args.interval)
    logger.info("Batch size: %d", args.batch_size)
    logger.info("Log level: %s", args.log_level)
    logger.info("=" * 60)
    
    # Create stop event
    stop_event = asyncio.Event()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum: int, frame: object) -> None:
        sig_name = signal.Signals(signum).name
        logger.info("Received signal %s, shutting down gracefully...", sig_name)
        stop_event.set()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the worker
    try:
        asyncio.run(run_worker(stop_event))
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as exc:
        logger.exception("Fatal error: %s", exc)
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Email worker shutdown complete.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
