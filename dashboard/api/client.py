"""Pure HTTP transport layer."""

import logging
from types import TracebackType
from typing import Any, Dict, Optional, Type

import httpx

from .exceptions import (APIConnectionError, APIError, APINotFoundError,
                         APIServerError, APITimeoutError)

logger = logging.getLogger(__name__)


class APIClient:
    """Pure HTTP client for backend API communication."""

    def __init__(self, base_url: str, timeout: int = 30, retries: int = 3):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the backend API
            timeout: Request timeout in seconds
            retries: Number of retry attempts for failed requests
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            data: Form data
            json: JSON payload

        Returns:
            Response data as dictionary

        Raises:
            APITimeoutError: If request times out
            APIConnectionError: If connection fails
            APINotFoundError: If resource not found (404)
            APIServerError: If server error (5xx)
            APIError: For other API errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Backend debug - console only
        logger.debug("API Request: %s %s", method, url)
        if params:
            logger.debug("Params: %s", params)
        if json:
            logger.debug("JSON: %s", json)

        for attempt in range(self.retries):
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                result = response.json()
                logger.debug("Status: %s", response.status_code)
                return result

            except httpx.TimeoutException as e:
                logger.warning(
                    "Timeout on attempt %d/%d: %s",
                    attempt + 1,
                    self.retries,
                    url,
                )
                if attempt == self.retries - 1:
                    raise APITimeoutError("Request timed out") from e
                continue

            except httpx.ConnectError as e:
                logger.warning(
                    "Connection error on attempt %d/%d: %s",
                    attempt + 1,
                    self.retries,
                    url,
                )
                if attempt == self.retries - 1:
                    raise APIConnectionError("Failed to connect to API") from e
                continue

            except httpx.HTTPStatusError as e:
                detail = e.response.text
                try:
                    error_data = e.response.json()
                    if "detail" in error_data:
                        detail = str(error_data["detail"])
                except ValueError:
                    # Response body wasn't valid JSON, keep raw text
                    pass

                logger.error("HTTP error %d: %s", e.response.status_code, detail)

                if e.response.status_code == 404:
                    raise APINotFoundError(f"Resource not found: {detail}") from e
                elif e.response.status_code == 422:
                    raise APIError(f"Validation error: {detail}") from e
                elif e.response.status_code >= 500:
                    raise APIServerError(f"Server error: {detail}") from e
                raise APIError(
                    f"Request failed: {e.response.status_code} - {detail}"
                ) from e

            except Exception as e:
                logger.exception("Unexpected error during API request")
                raise APIError(f"Unexpected error: {e}") from e

        # This should never be reached, but just in case
        raise APIError("Request failed after all retries")

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform GET request.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response data as dictionary
        """
        return self._make_request("GET", endpoint, params=params)

    def post(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform POST request.

        Args:
            endpoint: API endpoint path
            json: JSON payload
            data: Form data

        Returns:
            Response data as dictionary
        """
        return self._make_request("POST", endpoint, json=json, data=data)

    def put(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform PUT request.

        Args:
            endpoint: API endpoint path
            json: JSON payload
            data: Form data

        Returns:
            Response data as dictionary
        """
        return self._make_request("PUT", endpoint, json=json, data=data)

    def delete(
        self,
        endpoint: str,
    ) -> Dict[str, Any]:
        """
        Perform DELETE request.

        Args:
            endpoint: API endpoint path

        Returns:
            Response data as dictionary
        """
        return self._make_request("DELETE", endpoint)

    def patch(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform PATCH request.

        Args:
            endpoint: API endpoint path
            json: JSON payload
            data: Form data

        Returns:
            Response data as dictionary
        """
        return self._make_request("PATCH", endpoint, json=json, data=data)

    def close(self) -> None:
        """Close the client session."""
        self.client.close()

    def __enter__(self) -> "APIClient":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Exit context manager and close client."""
        self.close()
