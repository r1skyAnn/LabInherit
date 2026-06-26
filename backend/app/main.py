"""FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging

from pathlib import Path

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import (
    AppError,
    app_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.core.logging import configure_logging
from app.core.middleware import register_middlewares

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.tasks.email_worker import run_worker

    stop_event = asyncio.Event()
    worker_task = asyncio.create_task(run_worker(stop_event))
    logger.info("Email worker background task created.")
    yield
    stop_event.set()
    await worker_task


def create_app() -> FastAPI:
    # In dev environments, skip DNS/MX checks so that @*.local test accounts work.
    if settings.is_dev:
        try:
            import email_validator

            _original_validate = email_validator.validate_email

            def _dev_validate(email: str, **kwargs: object) -> object:  # type: ignore[no-redef]
                kwargs.setdefault("check_deliverability", False)
                kwargs.setdefault("test_environment", True)
                return _original_validate(email, **kwargs)

            email_validator.validate_email = _dev_validate  # type: ignore[attr-defined]

            # Also allow .local domains (blocked as "special-use" by default)
            for _attr in ("SPECIAL_USE_DOMAIN_NAMES", "SPECIAL_USE_DOMAIN_SUFFIXES"):
                _names = getattr(email_validator, _attr, None)
                if _names is not None:
                    _filtered = frozenset(n for n in _names if n != "local")
                    setattr(email_validator, _attr, _filtered)
        except Exception:
            pass

    configure_logging("DEBUG" if settings.APP_DEBUG else "INFO")

    app = FastAPI(
        title=settings.APP_NAME,
        version=__version__,
        debug=settings.APP_DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Global exception handlers (order matters — specific first)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    register_middlewares(app)

    # Serve uploaded images
    uploads_dir = Path(settings.UPLOAD_DIR)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

    app.include_router(api_v1_router, prefix="/api/v1")

    @app.get("/health", tags=["meta"], summary="Liveness probe")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    logger.info(
        "%s v%s started (env=%s, debug=%s)",
        settings.APP_NAME,
        __version__,
        settings.APP_ENV,
        settings.APP_DEBUG,
    )
    return app


app = create_app()
