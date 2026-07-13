# app/api/exception_handlers.py
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from config import get_logger

logger = get_logger()

__all__ = ["setup_exception_handlers"]


def _get_logger(request: Request) -> Any:
    """Get request-scoped logger or fallback to global logger."""
    return getattr(request.state, "logger", logger)


def _error_response(
    request: Request,
    status_code: int,
    detail: str,
    errors: Any = None,  # Type: Sequence[Any] from FastAPI
) -> JSONResponse:
    """Build consistent error response with request context."""
    content = {
        "detail": detail,
        "status_code": status_code,
        "path": request.url.path,
        "method": request.method,
        "request_id": getattr(request.state, "request_id", None),
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if errors is not None:
        content["errors"] = errors

    return JSONResponse(status_code=status_code, content=content)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed field information."""
    log = _get_logger(request)

    log.warning(
        "Validation failed",
        path=request.url.path,
        method=request.method,
        error_count=len(exc.errors()),
    )

    return _error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Validation error",
        errors=exc.errors(),
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors without exposing internals."""
    log = _get_logger(request)

    log.exception(
        "Database exception",
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
    )

    return _error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="A database error occurred. Please try again later.",
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper status codes."""
    log = _get_logger(request)

    # Log 5xx errors with stack trace, 4xx as warnings
    if exc.status_code >= 500:
        log.exception(
            "HTTP 5xx error",
            status_code=exc.status_code,
            path=request.url.path,
            method=request.method,
        )
    else:
        log.warning(
            "HTTP client error",
            status_code=exc.status_code,
            path=request.url.path,
            method=request.method,
            detail=exc.detail,
        )

    return _error_response(
        request=request,
        status_code=exc.status_code,
        detail=exc.detail,
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors without exposing internals."""
    log = _get_logger(request)

    log.exception(
        "Unexpected exception",
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
    )

    return _error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred. Please try again later.",
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI application."""
    # Note: FastAPI's ExceptionHandler type is more permissive than Pylance suggests.
    # These handlers work correctly at runtime despite type checker warnings.
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)  # type: ignore
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
    app.add_exception_handler(Exception, general_exception_handler)  # type: ignore
