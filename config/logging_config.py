# config/logging_config.py
import logging
import sys
from typing import Optional
from config.settings import settings


def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure application logging.
    
    Args:
        level: Optional log level override (defaults to settings.log_level)
    """
    log_level = getattr(logging, (level or settings.log_level).upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=settings.debug,  # Only force during development
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # Optional: Show SQLAlchemy queries in debug mode
    if settings.debug:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def get_logger(name: str = "job_market_api") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)