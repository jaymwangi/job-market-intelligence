# app/etl/extractors/jobs_api.py
"""Job listing extractor."""

from typing import Any

from app.etl.clients.http_client import HTTPClient


def mask_sensitive(value: str, show: int = 4) -> str:
    """Mask sensitive strings, showing only first few characters."""
    if not value:
        return "None"
    if len(value) <= show:
        return "*" * len(value)
    return f"{value[:show]}..."


def mask_params(params: dict[str, Any] | None) -> dict[str, str]:
    """Mask sensitive parameters for logging."""
    if not params:
        return {}

    masked = {}
    sensitive_keys = {"app_id", "app_key", "api_key", "key", "id", "secret", "password", "token"}

    for key, value in params.items():
        if key.lower() in sensitive_keys or any(s in key.lower() for s in sensitive_keys):
            masked[key] = mask_sensitive(str(value))
        else:
            masked[key] = str(value)

    return masked


class JobsExtractor:
    """Fetches job listings from external API."""

    def __init__(self, api_url: str, app_id: str, api_key: str, debug: bool = False):
        self.api_url = api_url
        self.app_id = app_id
        self.api_key = api_key
        self.debug = debug
        self.client = HTTPClient(debug=debug)

    def fetch_page(self, page: int = 1, results_per_page: int = 10) -> dict[str, Any]:
        """Fetch one page of job listings."""
        # Page is in the URL path, not as a query parameter
        params = {
            "app_id": self.app_id,
            "app_key": self.api_key,
            "results_per_page": results_per_page,
        }

        # URL path includes the page number
        url = f"{self.api_url}/jobs/gb/search/{page}"

        # Only print debug info if enabled
        if self.debug:
            print(f"📍 URL: {url}")
            print(f"📦 Params: {mask_params(params)}")

        return self.client.get(url, params=params)
