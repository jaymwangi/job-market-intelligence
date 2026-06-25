# config/logging_config.py
import logging
import sys
from typing import Optional

from config import settings


def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Optional log level override. If not provided, uses settings.LOG_LEVEL.
    """
    log_level = level or settings.log_level
    
    # Convert string to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # For development, show SQLAlchemy queries
    if settings.debug:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)