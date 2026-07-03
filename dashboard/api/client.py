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
    """Pure HTTP transport layer."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a GET request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Backend debug - console only
        print(f"🌐 API Request: GET {url}")
        if params:
            print(f"   Params: {params}")
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
                print(f"   ✅ Status: {response.status_code}")
                return result
        except httpx.TimeoutException:
            print(f"   ❌ Timeout")
            raise APITimeoutError("Request timed out")
        except httpx.ConnectError:
            print(f"   ❌ Connection failed")
            raise APIConnectionError("Failed to connect to API")
        except httpx.HTTPStatusError as e:
            print(f"   ❌ Status: {e.response.status_code}")
            detail = e.response.text
            try:
                error_data = e.response.json()
                if "detail" in error_data:
                    detail = str(error_data["detail"])
                    print(f"   Detail: {detail}")
            except:
                pass
            
            if e.response.status_code == 404:
                raise APINotFoundError(f"Resource not found: {detail}")
            elif e.response.status_code == 422:
                raise APIError(f"Validation error: {detail}")
            elif e.response.status_code >= 500:
                raise APIServerError(f"Server error: {detail}")
            raise APIError(f"Request failed: {e.response.status_code} - {detail}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {str(e)}")
            raise APIError(f"Unexpected error: {str(e)}")