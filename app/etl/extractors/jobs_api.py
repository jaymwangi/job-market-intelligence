# app/etl/extractors/jobs_api.py
"""Job listing extractor."""

from typing import Dict, Any
from app.etl.clients.http_client import HTTPClient


class JobsExtractor:
    """Fetches job listings from external API."""
    
    def __init__(self, api_url: str, app_id: str, api_key: str):
        self.api_url = api_url
        self.app_id = app_id
        self.api_key = api_key
        self.client = HTTPClient()
    
    def fetch_page(self, page: int = 1, results_per_page: int = 10) -> Dict[str, Any]:
        """Fetch one page of job listings."""
        # Page is in the URL path, not as a query parameter
        params = {
            "app_id": self.app_id,
            "app_key": self.api_key,
            "results_per_page": results_per_page,
            # Removed: "page": page  ← This was causing the 400
        }
        
        # URL path includes the page number
        url = f"{self.api_url}/jobs/gb/search/{page}"
        
        print(f"📍 URL: {url}")
        print(f"📦 Params: {params}")
        
        return self.client.get(url, params=params)