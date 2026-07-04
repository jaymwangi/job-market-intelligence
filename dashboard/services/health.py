# dashboard/services/health.py
"""Health check service."""
from dashboard.api import HEALTH
from dashboard.services.base import BaseService
from dashboard.schemas.health import HealthResponse
import logging

logger = logging.getLogger(__name__)


class HealthService(BaseService):
    """Service for health operations."""
    
    def check(self) -> HealthResponse:
        """Check API health."""
        try:
            # Use self.api_client (from BaseService)
            data = self.api_client.get(HEALTH)
            
            # The API returns: {"status": "healthy", "database": "connected", ...}
            # We only care about the status field
            return HealthResponse(status=data.get("status", "unknown"))
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            # Return unhealthy status
            return HealthResponse(status="unhealthy")
    
    def is_healthy(self) -> bool:
        """Quick check if API is healthy."""
        try:
            result = self.check()
            return result.status == "healthy"
        except Exception:
            return False