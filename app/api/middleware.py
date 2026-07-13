import time
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from config.logging_config import get_logger
from config.settings import settings

# Import metrics collector with fallback
try:
    from app.core.metrics import metrics_collector
except ImportError:
    # Fallback if metrics module doesn't exist yet
    class DummyMetricsCollector:
        def record_request(self, endpoint, status_code, duration_ms):
            pass

    metrics_collector = DummyMetricsCollector()


# Module-level constants (safe access with getattr)
EXCLUDED_PATHS = frozenset(getattr(settings, "logging_excluded_paths", []))


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for request logging with correlation IDs and metrics.

    Features:
    - Generates/accepts X-Request-ID for request tracing
    - Logs request start with method, path, client info
    - Logs request completion with status code, duration, size
    - Attaches logger to request.state for endpoint use
    - Measures request duration with high precision
    - Excludes health/metrics endpoints from logging (configurable)
    - Records operational metrics for monitoring

    Usage in main.py:
        from app.api.middleware import RequestLoggingMiddleware
        app.add_middleware(RequestLoggingMiddleware)
    """

    async def dispatch(self, request: Request, call_next):
        # Use existing X-Request-ID or generate a new one
        request_id = request.headers.get("X-Request-ID", str(uuid4()))

        # Set request ID on request state
        request.state.request_id = request_id

        # Get logger with stable component name
        log = get_logger(
            component="http",
            request_id=request_id,
        )

        # Attach logger to request state for endpoints
        request.state.logger = log

        # Store start time for potential use by other middleware
        start_time = time.perf_counter()

        # Determine endpoint path for metrics
        endpoint = request.url.path

        # Check if this path should be logged (using pre-computed frozenset)
        should_log = request.url.path not in EXCLUDED_PATHS

        # Log request start with structured fields (skip for health checks)
        if should_log:
            log.info(
                "Request started",
                method=request.method,
                path=request.url.path,
                client_host=request.client.host if request.client else None,
                client_port=request.client.port if request.client else None,
            )

            # Only log user-agent and query params in debug mode
            if settings.debug:
                log.debug(
                    "Request details",
                    user_agent=request.headers.get("user-agent"),
                    query_params=str(request.query_params) if request.query_params else None,
                )

        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Record metrics (only for API endpoints, skip health checks)
            if endpoint.startswith(settings.api_prefix):
                metrics_collector.record_request(
                    endpoint=endpoint, status_code=response.status_code, duration_ms=duration_ms
                )

            # Add request ID to response headers (always)
            response.headers["X-Request-ID"] = request_id

            # Log response with appropriate level based on status code
            if should_log:
                duration_ms_rounded = round(duration_ms, 2)

                # Log at appropriate level based on status code
                if response.status_code >= 500:
                    log.error(
                        "Request completed with server error",
                        status_code=response.status_code,
                        duration_ms=duration_ms_rounded,
                        content_length=response.headers.get("content-length"),
                        method=request.method,
                        path=request.url.path,
                    )
                elif response.status_code >= 400:
                    log.warning(
                        "Request completed with client error",
                        status_code=response.status_code,
                        duration_ms=duration_ms_rounded,
                        content_length=response.headers.get("content-length"),
                        method=request.method,
                        path=request.url.path,
                    )
                else:
                    log.info(
                        "Request completed",
                        status_code=response.status_code,
                        duration_ms=duration_ms_rounded,
                        content_length=response.headers.get("content-length"),
                        method=request.method,
                        path=request.url.path,
                    )

            return response

        except Exception as exc:
            # Record error metrics
            duration_ms = (time.perf_counter() - start_time) * 1000
            if endpoint.startswith(settings.api_prefix):
                metrics_collector.record_request(
                    endpoint=endpoint, status_code=500, duration_ms=duration_ms
                )

            # Log exception with full context (always, even for excluded paths)
            duration_ms_rounded = round(duration_ms, 2)
            log.exception(
                "Request failed",
                error_type=type(exc).__name__,
                duration_ms=duration_ms_rounded,
                path=request.url.path,
                method=request.method,
            )
            raise


def setup_middleware(app: FastAPI) -> FastAPI:
    """
    Configure all middleware for the FastAPI application.

    ⚠️ IMPORTANT: Middleware execution order in FastAPI/Starlette
    is REVERSE of registration order.

    Registration order (bottom to top):
    1. RequestLoggingMiddleware (registered last, executes first)
    2. GZipMiddleware
    3. TrustedHostMiddleware (production only)
    4. CORSMiddleware (registered first, executes last)

    Request Flow (outer → inner):
        RequestLoggingMiddleware → GZipMiddleware → TrustedHostMiddleware → CORSMiddleware → Route

    Response Flow (inner → outer):
        Route → CORSMiddleware → TrustedHostMiddleware → GZipMiddleware → RequestLoggingMiddleware

    Args:
        app: FastAPI application instance

    Returns:
        FastAPI application with middleware configured

    Example:
        from app.api.middleware import setup_middleware
        app = setup_middleware(app)
    """

    # --- 1. CORSMiddleware (Innermost - registered first) ---
    # Runs last on request, first on response
    # Handles CORS headers for cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, "allowed_origins", ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
        max_age=600,  # Cache preflight requests for 10 minutes
    )

    # --- 2. TrustedHostMiddleware (Production Only) ---
    # Validates Host header to prevent host header attacks
    # Only enabled in production to avoid development host issues
    if getattr(settings, "environment", "development") == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=getattr(settings, "allowed_hosts", ["*"]),
        )

    # --- 3. GZipMiddleware ---
    # Compresses responses larger than 1KB
    # Improves performance for JSON APIs
    app.add_middleware(
        GZipMiddleware,
        minimum_size=1000,
    )

    # --- 4. RequestLoggingMiddleware (Outermost - registered last) ---
    # ⚠️ Registered LAST so it executes FIRST
    # Wraps ALL other middleware to capture the complete request lifecycle
    # Logs request start/end, timing, and status
    app.add_middleware(RequestLoggingMiddleware)

    return app


# --- Helper Functions ---


def get_request_context(request: Request) -> dict[str, str]:
    """
    Extract request context for use in background tasks.

    Args:
        request: FastAPI request object

    Returns:
        Dictionary with request_id for correlation

    Example:
        from app.api.middleware import get_request_context
        context = get_request_context(request)
        background_tasks.add_task(process_data, context=context)
    """
    return {
        "request_id": getattr(request.state, "request_id", "-"),
    }


def get_task_logger(request: Request, task_name: str):
    """
    Create a logger for background tasks with request context.

    Args:
        request: FastAPI request object
        task_name: Name of the background task

    Returns:
        Logger instance bound with task context

    Example:
        log = get_task_logger(request, "email_sender")
        log.info("Sending email", recipient="user@example.com")
    """
    request_id = getattr(request.state, "request_id", "-")
    return get_logger(
        component="task",
        request_id=request_id,
    ).bind(task=task_name)


def log_elapsed_time(request: Request, operation: str, start_time: float):
    """
    Log elapsed time for an operation within a request.

    Args:
        request: FastAPI request object
        operation: Name of the operation being timed
        start_time: Start time from time.perf_counter()

    Example:
        start = time.perf_counter()
        # ... do work ...
        log_elapsed_time(request, "database_query", start)
    """
    log = getattr(request.state, "logger", None)
    if log:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        log.info(
            "Operation completed",
            operation=operation,
            duration_ms=duration_ms,
        )
