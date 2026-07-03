from api.client import APIClient
from core.config import settings

class BaseService:
    """Base service with API client."""
    
    def __init__(self):
        self._client = APIClient(
            base_url=settings.API_BASE_URL,
            timeout=settings.API_TIMEOUT
        )
    
    @property
    def client(self) -> APIClient:
        return self._client