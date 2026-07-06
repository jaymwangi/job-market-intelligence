# dashboard/utils/logging.py
"""Centralized logging configuration."""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Set specific log levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


# Log performance metrics
def log_performance(operation: str, duration: float) -> None:
    """Log performance metrics."""
    logger = get_logger("performance")
    logger.info(f"{operation} took {duration:.2f}s")


# Log API calls
def log_api_call(endpoint: str, status: int, duration: float) -> None:
    """Log API call details."""
    logger = get_logger("api")
    logger.debug(f"{endpoint} → {status} ({duration:.2f}s)")
