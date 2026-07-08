# app/etl/clients/http_client.py
"""Simple HTTP client with session reuse."""

from typing import Any

import requests


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


class HTTPClient:
    """Minimal HTTP client with GET support and session reuse."""

    def __init__(self, timeout: int = 30, debug: bool = False):
        self.timeout = timeout
        self.debug = debug
        self.session = requests.Session()
        # Set default headers to match Swagger
        self.session.headers.update(
            {
                "Accept": "application/json",
            }
        )

    def get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send GET request and return JSON response."""
        # Debug logging (only if enabled)
        if self.debug:
            print("\n🔍 Request Details:")
            print(f"  URL: {url}")
            print(f"  Params: {mask_params(params)}")
            print(f"  Headers: {dict(self.session.headers)}")

        response = self.session.get(url, params=params, timeout=self.timeout)

        # Detailed error reporting (always enabled for errors)
        if not response.ok:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(f"📍 Full URL: {response.url}")
            print(f"📝 Response: {response.text}")
            print(f"🔧 Request Headers: {response.request.headers}")

        response.raise_for_status()
        return response.json()
