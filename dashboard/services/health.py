from services.base import BaseService
from api.endpoints import endpoints
from schemas.health import HealthResponse

class HealthService(BaseService):
    """Service for health operations."""
    
    def check(self) -> HealthResponse:
        """Check API health."""
        data = self.client.get(endpoints.HEALTH)
        return HealthResponse(**data)