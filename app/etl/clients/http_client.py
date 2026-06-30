# app/etl/clients/http_client.py
"""Simple HTTP client with session reuse."""

import requests
from typing import Optional, Dict, Any


class HTTPClient:
    """Minimal HTTP client with GET support and session reuse."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        # Set default headers to match Swagger
        self.session.headers.update({
            "Accept": "application/json",
        })
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send GET request and return JSON response."""
        print(f"\n🔍 Request Details:")
        print(f"  URL: {url}")
        print(f"  Params: {params}")
        print(f"  Headers: {dict(self.session.headers)}")
        
        response = self.session.get(url, params=params, timeout=self.timeout)
        
        # Detailed error reporting
        if not response.ok:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(f"📍 Full URL: {response.url}")
            print(f"📝 Response: {response.text}")
            print(f"🔧 Request Headers: {response.request.headers}")
        
        response.raise_for_status()
        return response.json()