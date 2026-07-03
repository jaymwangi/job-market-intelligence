import httpx
from typing import Dict, Any, Optional

from .exceptions import (
    APIError,
    APIConnectionError,
    APITimeoutError,
    APIServerError,
    APINotFoundError,
)

class APIClient:
    """Simple HTTP client for API communication."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a GET request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            raise APITimeoutError("Request timed out")
        except httpx.ConnectError:
            raise APIConnectionError("Failed to connect to API")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise APINotFoundError("Resource not found")
            elif e.response.status_code >= 500:
                raise APIServerError("Server error")
            raise APIError(f"Request failed: {e.response.status_code}")