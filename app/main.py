import os
import platform
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from starlette.routing import Route, WebSocketRoute

from app.api.exception_handlers import setup_exception_handlers
from app.api.middleware import setup_middleware
from app.api.router import api_router
from config import settings
from config.logging_config import get_logger

# Logging is already configured in config.logging_config
logger = get_logger("lifespan")

# Constants
VALID_ENVIRONMENTS = {"development", "staging", "production"}


def validate_configuration() -> None:
    """
    Validate application configuration on startup.

    Raises:
        ValueError: If required configuration is missing or invalid.
    """
    errors = []

    # Validate database URL - use sqlalchemy_database_url
    if not settings.sqlalchemy_database_url:
        errors.append("Database URL is not configured")

    # Validate API prefix
    if not settings.api_prefix.startswith("/"):
        errors.append(f"API prefix must start with '/': {settings.api_prefix}")

    # Validate environment
    if settings.environment not in VALID_ENVIRONMENTS:
        errors.append(
            f"Invalid environment: {settings.environment}. "
            f"Must be one of: {', '.join(VALID_ENVIRONMENTS)}"
        )

    # Validate pool settings
    if settings.db_pool_size <= 0:
        errors.append(f"db_pool_size must be > 0: {settings.db_pool_size}")

    if settings.db_max_overflow < 0:
        errors.append(f"db_max_overflow must be >= 0: {settings.db_max_overflow}")

    # Validate API metadata
    if not settings.api_title:
        errors.append("api_title is not set")

    if not settings.api_version:
        errors.append("api_version is not set")

    # Validate allowed origins (if not in debug mode)
    if settings.is_production() and "*" in settings.allowed_origins:
        errors.append("Wildcard origins not allowed in production")

    # Run production-specific validation
    if settings.is_production():
        production_errors = settings.validate_production()
        errors.extend(production_errors)

    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Log successful validation
    logger.info(
        "Configuration validated successfully",
        environment=settings.environment,
        api_prefix=settings.api_prefix,
        pool_size=settings.db_pool_size,
        is_production=settings.is_production(),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.

    Handles startup and shutdown events with structured logging.
    """
    # Bind common context for startup logs
    startup_log = logger.bind(
        app_name=settings.app_name,
        version=settings.api_version,
        environment=settings.environment,
    )

    # Startup
    startup_log.info(
        "Application starting",
        debug=settings.debug,
        host=settings.host,
        port=settings.port,
        python_version=platform.python_version(),
        pid=os.getpid(),
    )

    # Validate configuration (fail fast if something is wrong)
    try:
        validate_configuration()
    except ValueError as e:
        startup_log.error("Startup failed due to configuration error", error=str(e))
        raise

    # Initialize database connections
    try:
        from app.database.session import engine

        startup_log.info("Database engine initialized", pool_size=settings.db_pool_size)
    except ImportError as e:
        startup_log.warning("Database engine not available", error=str(e))

    yield

    # Shutdown
    startup_log.info("Application shutting down")

    # Clean up database connections
    try:
        from app.database.session import engine

        # Check if engine is async or sync
        if hasattr(engine, "dispose") and callable(engine.dispose):
            # For sync engine
            engine.dispose()
        startup_log.info("Database connections closed")
    except ImportError:
        pass


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    # Determine if docs should be enabled
    is_production = settings.is_production()
    docs_enabled = not is_production

    # Build servers list (only for development)
    servers = (
        [
            {
                "url": f"http://localhost:{settings.port}",
                "description": "Local Development Server",
            }
        ]
        if settings.debug
        else None
    )

    # Create FastAPI application
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
        lifespan=lifespan,
        servers=servers,
        contact={
            "name": "James Mwangi",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_tags=(
            [
                {"name": "Health", "description": "Health check and monitoring endpoints"},
                {"name": "Jobs", "description": "Job search, filtering, and retrieval operations"},
                {"name": "Analytics", "description": "Analytics and insights about the job market"},
            ]
            if docs_enabled
            else None
        ),
    )

    # --- Setup Exception Handlers ---
    # Global exception handlers with request-scoped logging
    setup_exception_handlers(app)

    # --- Setup Middleware ---
    # Includes: RequestLogging, GZip, TrustedHost (production), CORS
    setup_middleware(app)

    # --- Include API Routes ---
    app.include_router(api_router, prefix=settings.api_prefix)

    return app


# Create application instance
app = create_app()


# --- Root Endpoint ---


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """
    Root endpoint with API information.

    Returns:
        API metadata including name, version, and documentation links.
    """
    is_production = settings.is_production()
    docs_enabled = not is_production

    response: dict = {
        "name": settings.api_title,
        "version": settings.api_version,
        "environment": settings.environment,
        "status": "running",
        "health": f"{settings.api_prefix}/health",
        "api_prefix": settings.api_prefix,
    }

    # Only include docs URLs if they're enabled and not None
    if docs_enabled:
        # Use getattr with default to ensure we have string values
        docs_url = getattr(app, "docs_url", None)
        redoc_url = getattr(app, "redoc_url", None)
        openapi_url = getattr(app, "openapi_url", None)

        if docs_url is not None:
            response["docs"] = docs_url
        if redoc_url is not None:
            response["redoc"] = redoc_url
        if openapi_url is not None:
            response["openapi"] = openapi_url

    return response


# --- Optional: Development-only endpoints ---

if settings.debug:
    from fastapi import Request

    @app.get("/debug/headers", include_in_schema=False)
    async def debug_headers(request: Request):
        """
        Debug endpoint to inspect request headers.
        Only available in debug mode.
        """
        return {
            "headers": dict(request.headers),
            "request_id": getattr(request.state, "request_id", "-"),
        }

    @app.get("/debug/time", include_in_schema=False)
    async def debug_time():
        """
        Debug endpoint to check server time.
        Only available in debug mode.
        """
        return {
            "utc_time": datetime.now(UTC).isoformat(),
            "timezone": "UTC",
        }

    @app.get("/debug/ping", include_in_schema=False)
    async def debug_ping():
        """
        Simple ping endpoint for connectivity testing.
        Only available in debug mode.
        """
        return {"pong": True, "timestamp": datetime.now(UTC).isoformat()}

    @app.get("/debug/routes", include_in_schema=False)
    async def debug_routes():
        """
        Debug endpoint to list all registered routes.
        Only available in debug mode.
        """
        routes = []
        for route in app.routes:
            # Build route info based on route type
            route_info: dict = {
                "type": type(route).__name__,
            }

            # Handle HTTP routes (Route)
            if isinstance(route, Route):
                route_info["path"] = route.path
                route_info["name"] = route.name
                route_info["methods"] = sorted(route.methods or [])

            # Handle WebSocket routes
            elif isinstance(route, WebSocketRoute):
                route_info["path"] = route.path
                route_info["name"] = route.name
                route_info["methods"] = ["WEBSOCKET"]

            # Handle other route types (APIRoute, etc.)
            else:
                route_info["path"] = getattr(route, "path", None)
                route_info["name"] = getattr(route, "name", None)
                methods = getattr(route, "methods", set())
                route_info["methods"] = sorted(methods or [])

            routes.append(route_info)

        return {"routes": routes, "count": len(routes)}
