# dashboard/api/client.py
"""Pure HTTP transport layer."""
import httpx
from typing import Dict, Any, Optional
from urllib.parse import urljoin
import logging

from .exceptions import (
    APIError,
    APIConnectionError,
    APITimeoutError,
    APIServerError,
    APINotFoundError,
)

logger = logging.getLogger(__name__)


class APIClient:
    """Pure HTTP client for backend API communication."""
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        retries: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.retries = retries
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Backend debug - console only
        print(f"🌐 API Request: {method} {url}")
        if params:
            print(f"   Params: {params}")
        if json:
            print(f"   JSON: {json}")
        
        for attempt in range(self.retries):
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                print(f"   ✅ Status: {response.status_code}")
                return result
            except httpx.TimeoutException:
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.retries}: {url}")
                print(f"   ⏱️ Timeout (attempt {attempt + 1}/{self.retries})")
                if attempt == self.retries - 1:
                    print(f"   ❌ Timeout")
                    raise APITimeoutError("Request timed out")
            except httpx.ConnectError:
                logger.warning(f"Connection error on attempt {attempt + 1}/{self.retries}: {url}")
                print(f"   🔌 Connection failed (attempt {attempt + 1}/{self.retries})")
                if attempt == self.retries - 1:
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
                
                logger.error(f"HTTP error {e.response.status_code}: {detail}")
                
                if e.response.status_code == 404:
                    raise APINotFoundError(f"Resource not found: {detail}")
                elif e.response.status_code == 422:
                    raise APIError(f"Validation error: {detail}")
                elif e.response.status_code >= 500:
                    raise APIServerError(f"Server error: {detail}")
                raise APIError(f"Request failed: {e.response.status_code} - {detail}")
            except Exception as e:
                print(f"   ❌ Unexpected error: {str(e)}")
                logger.error(f"Unexpected error: {e}")
                raise APIError(f"Unexpected error: {str(e)}")
        
        # This should never be reached, but just in case
        raise APIError("Request failed after all retries")
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Perform GET request."""
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, json: Optional[Dict] = None) -> Dict[str, Any]:
        """Perform POST request."""
        return self._make_request('POST', endpoint, json=json)
    
    def close(self):
        """Close the client session."""
        self.client.close()