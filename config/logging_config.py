# config/logging_config.py
import sys
import logging
from loguru import logger
from config.settings import settings


def setup_logging():
    """
    Configure colored logging with loguru.
    """
    # Remove default handler
    logger.remove()
    
    # Determine log level
    log_level = settings.log_level.upper()
    
    # Console handler with colors
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=settings.debug,
    )
    
    # File handler (no colors, rotated)
    logger.add(
        "logs/app.log",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}",
        level="INFO",
    )
    
    # Error file handler
    logger.add(
        "logs/errors.log",
        rotation="100 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}",
        level="ERROR",
    )
    
    # Control SQLAlchemy logging
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    
    if settings.debug:
        # In DEBUG mode, show SQL queries
        sqlalchemy_logger.setLevel(logging.INFO)
        logger.info("SQLAlchemy SQL logging enabled (DEBUG mode)")
    else:
        # In production, suppress SQL queries
        sqlalchemy_logger.setLevel(logging.WARNING)
    
    # Suppress other noisy loggers
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
    
    # Log startup
    logger.info(f"Logging initialized with level: {log_level}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"SQL logging: {'Enabled' if settings.debug else 'Disabled'}")
    
    return logger


def get_logger(name: str = "job_market_api"):
    """
    Get a logger instance.
    
    Args:
        name: Logger name (used for context)
    
    Returns:
        Logger instance bound with name
    """
    return logger.bind(name=name)


# Initialize logging when module is imported
logger = setup_logging()