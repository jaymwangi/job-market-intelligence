from dashboard.api import HEALTH
from dashboard.services.base import BaseService
from dashboard.schemas.health import HealthResponse


class HealthService(BaseService):
    """Service for health operations."""
    
    def check(self) -> HealthResponse:
        """Check API health."""
        data = self.api.get(HEALTH)  # Use self.api, not self.client
        return HealthResponse(**data)