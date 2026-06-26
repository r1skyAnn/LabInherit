"""Custom exception types and a global exception handler.

All business code should raise `AppError` subclasses; the handler converts
them to a consistent JSON envelope and chooses the right HTTP status code.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application error. Subclasses set status_code and default message."""

    status_code: int = 500
    code: str = "internal_error"
    default_message: str = "Internal server error"

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message or self.default_message)
        self.message = message or self.default_message
        self.details = details or {}


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    default_message = "Resource not found"


class PermissionDeniedError(AppError):
    status_code = 403
    code = "permission_denied"
    default_message = "Permission denied"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    default_message = "Authentication required"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    default_message = "Resource conflict"


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"
    default_message = "Invalid input"


def _envelope(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        }
    }


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning(
        "AppError on %s %s: %s (%s)",
        request.method,
        request.url.path,
        exc.message,
        exc.code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(code=exc.code, message=exc.message, details=exc.details),
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning("Validation error: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content=_envelope(
            code="validation_error",
            message="Request validation failed",
            details={"errors": exc.errors()},
        ),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=_envelope(
            code="internal_error",
            message="Internal server error",
        ),
    )
