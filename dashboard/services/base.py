# dashboard/services/base.py
"""Base service with shared infrastructure from Sprint 5.1."""

import logging

from api.client import APIClient

# Import CacheManager directly, not through __init__
from utils.cache import CacheManager

logger = logging.getLogger(__name__)


class BaseService:
    """Base service with shared infrastructure."""

    def __init__(self, api_client: APIClient, cache_manager: CacheManager | None = None):
        self.api_client = api_client
        self.cache_manager = cache_manager or CacheManager()

    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle and log errors consistently."""
        logger.error(f"Error in {context}: {str(error)}")
        raise

    def refresh(self) -> None:
        """Refresh service state - override in subclasses."""
        if self.cache_manager:
            self.cache_manager.clear()
