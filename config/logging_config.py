# config/logging_config.py
import logging
import sys
from pathlib import Path

from loguru import logger

from config.settings import settings

__all__ = ["logger", "get_logger", "setup_logging"]


def _add_defaults(record):
    """Add default fields to every log record."""
    record["extra"].setdefault("service", settings.app_name)
    record["extra"].setdefault("environment", settings.environment)
    record["extra"].setdefault("version", settings.api_version)
    record["extra"].setdefault("request_id", "-")
    record["extra"].setdefault("component", "app")
    return record


def setup_logging():
    """
    Configure production-ready logging with loguru.

    Features:
    - UTC timestamps with milliseconds
    - JSON logs in production (for cloud logging)
    - Colored console logs in development
    - Request ID support via binding
    - Environment-aware configuration
    - No file logging in production (use stdout only)
    - Default fields injected for all loggers
    """
    # Declare that we're modifying the global logger
    global logger

    # Remove default handler
    logger.remove()

    # Determine log level
    log_level = settings.log_level.upper()
    is_production = settings.environment == "production"

    # Get logs directory (with fallback)
    logs_dir = getattr(settings, "logs_dir", "logs")
    log_path = Path(logs_dir)

    # --- Configure Sinks on Global Logger ---
    if is_production:
        # Production: JSON logs for cloud logging systems
        logger.add(
            sys.stdout,
            serialize=True,
            level=log_level,
            backtrace=settings.debug,
            diagnose=settings.debug,
        )
    else:
        # Development: Pretty colored console with process/thread IDs
        logger.add(
            sys.stdout,
            format=(
                "<green>{time:YYYY-MM-DDTHH:mm:ss.SSSZZ}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{extra[component]}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<yellow>{extra[request_id]}</yellow> | "
                "{process.id}:{thread.id} | "
                "<level>{message}</level>"
            ),
            level=log_level,
            colorize=True,
            backtrace=settings.debug,
            diagnose=settings.debug,
        )

        # Create logs directory (development only)
        log_path.mkdir(parents=True, exist_ok=True)

        # General application log (rotated)
        logger.add(
            log_path / "app.log",
            rotation="500 MB",
            retention="10 days",
            compression="zip",
            format="{time:YYYY-MM-DDTHH:mm:ss.SSSZZ} | {level: <8} | {extra[component]} | {extra[request_id]} | {process.id}:{thread.id} | {message}",
            level="INFO",
        )

        # Error-specific log
        logger.add(
            log_path / "errors.log",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            format="{time:YYYY-MM-DDTHH:mm:ss.SSSZZ} | {level: <8} | {extra[component]} | {extra[request_id]} | {process.id}:{thread.id} | {message}",
            level="ERROR",
        )

    # --- Control External Loggers ---
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")

    if settings.debug:
        sqlalchemy_logger.setLevel(logging.INFO)
    else:
        sqlalchemy_logger.setLevel(logging.WARNING)

    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)

    # Check if disable_uvicorn_access_logs exists in settings
    if getattr(settings, "disable_uvicorn_access_logs", False):
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # --- Intercept Standard Logging ---
    class InterceptHandler(logging.Handler):
        """Forward standard logging records to Loguru."""

        def emit(self, record):
            # Get corresponding Loguru level
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from stack with proper type checking
            frame = logging.currentframe()
            depth = 2
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # --- Patch Global Logger with Default Fields ---
    # This ensures ALL loggers automatically include these fields
    # Use logger.patch which returns a new logger, then reassign
    patched_logger = logger.patch(_add_defaults)

    # Reassign the global logger
    logger = patched_logger

    # Log startup (just one event - lifespan handles the rest)
    logger.info(
        "Logging system initialized",
        log_level=log_level,
        json_logs=is_production,
        logs_dir=str(log_path) if not is_production else "stdout only",
    )


def get_logger(component: str = "app", request_id: str | None = None):
    """
    Get a logger instance with context binding.

    Args:
        component: Component name for log context (e.g., "users", "auth", "db")
        request_id: Optional request ID for correlation

    Returns:
        Logger instance bound with component and request_id

    Example:
        log = get_logger("users_service", request_id="abc-123")
        log.info("Processing user request", user_id=123)
    """
    if request_id:
        return logger.bind(component=component, request_id=request_id)
    return logger.bind(component=component)


# Configure logging when module is imported
setup_logging()
