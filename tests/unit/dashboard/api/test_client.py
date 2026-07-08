"""
Unit tests for dashboard API client.
"""

from unittest.mock import Mock

import httpx
import pytest

from dashboard.api.client import APIClient
from dashboard.api.exceptions import (
    APIConnectionError,
    APIError,
    APINotFoundError,
    APIServerError,
    APITimeoutError,
)


class TestAPIClient:
    """Test suite for API client."""

    @pytest.fixture
    def client(self):
        """Create an API client instance."""
        return APIClient(base_url="https://api.test.com", timeout=30, retries=3)

    def test_init(self, client):
        """Test client initialization."""
        assert client.base_url == "https://api.test.com"
        assert client.timeout == 30
        assert client.retries == 3
        assert client.client is not None

    def test_get_success(self, client, mocker):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = Mock()

        mock_request = mocker.patch.object(client.client, "request")
        mock_request.return_value = mock_response

        result = client.get("/test")
        assert result == {"data": "test"}
        mock_request.assert_called_once()

    def test_get_with_params(self, client, mocker):
        """Test GET request with query parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = Mock()

        mock_request = mocker.patch.object(client.client, "request")
        mock_request.return_value = mock_response

        result = client.get("/test", params={"key": "value"})
        assert result == {"data": "test"}
        mock_request.assert_called_with(
            method="GET",
            url="https://api.test.com/test",
            params={"key": "value"},
            data=None,
            json=None,
            timeout=30,
        )

    def test_post_success(self, client, mocker):
        """Test successful POST request."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1}
        mock_response.raise_for_status = Mock()

        mock_request = mocker.patch.object(client.client, "request")
        mock_request.return_value = mock_response

        result = client.post("/test", json={"name": "test"})
        assert result == {"id": 1}

    def test_put_success(self, client, mocker):
        """Test successful PUT request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "updated": True}
        mock_response.raise_for_status = Mock()

        mock_request = mocker.patch.object(client.client, "request")
        mock_request.return_value = mock_response

        result = client.put("/test/1", json={"name": "updated"})
        assert result == {"id": 1, "updated": True}

    def test_delete_success(self, client, mocker):
        """Test successful DELETE request."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()

        mock_request = mocker.patch.object(client.client, "request")
        mock_request.return_value = mock_response

        result = client.delete("/test/1")
        assert result == {}

    def test_patch_success(self, client, mocker):
        """Test successful PATCH request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "patched": True}
        mock_response.raise_for_status = Mock()

        mock_request = mocker.patch.object(client.client, "request")
        mock_request.return_value = mock_response

        result = client.patch("/test/1", json={"field": "value"})
        assert result == {"id": 1, "patched": True}

    def test_timeout_error(self, client, mocker):
        """Test timeout error handling."""
        mock_request = mocker.patch.object(client.client, "request")
        mock_request.side_effect = httpx.TimeoutException("Timeout")

        with pytest.raises(APITimeoutError):
            client.get("/test")

    def test_connection_error(self, client, mocker):
        """Test connection error handling."""
        mock_request = mocker.patch.object(client.client, "request")
        mock_request.side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(APIConnectionError):
            client.get("/test")

    def test_not_found_error(self, client, mocker):
        """Test 404 error handling."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.json.return_value = {"detail": "Resource not found"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=Mock(), response=mock_response
        )

        mock_request = mocker.patch.object(client.client, "request")
        mock_request.return_value = mock_response

        with pytest.raises(APINotFoundError):
            client.get("/test/999")

    def test_server_error(self, client, mocker):
        """Test 500 error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_response.json.return_value = {"detail": "Internal server error"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=Mock(), response=mock_response
        )

        mock_request = mocker.patch.object(client.client, "request")
        mock_request.return_value = mock_response

        with pytest.raises(APIServerError):
            client.get("/test")

    def test_validation_error(self, client, mocker):
        """Test 422 validation error handling."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.text = "Validation Error"
        mock_response.json.return_value = {"detail": "Invalid data"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "422", request=Mock(), response=mock_response
        )

        mock_request = mocker.patch.object(client.client, "request")
        mock_request.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            client.get("/test")
        assert "Validation error" in str(exc_info.value)

    def test_retry_logic(self, client, mocker):
        """Test retry logic on failure."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "success"}
        mock_response.raise_for_status = Mock()

        mock_request = mocker.patch.object(client.client, "request")
        # First attempt fails, second succeeds
        mock_request.side_effect = [httpx.TimeoutException("Timeout"), mock_response]

        result = client.get("/test")
        assert result == {"data": "success"}
        assert mock_request.call_count == 2

    def test_retry_all_fail(self, client, mocker):
        """Test retry logic when all attempts fail."""
        mock_request = mocker.patch.object(client.client, "request")
        mock_request.side_effect = httpx.TimeoutException("Timeout")

        with pytest.raises(APITimeoutError):
            client.get("/test")
        assert mock_request.call_count == client.retries

    def test_context_manager(self, client, mocker):
        """Test context manager support."""
        mock_close = mocker.patch.object(client.client, "close")
        with client as c:
            assert c is client
        mock_close.assert_called_once()

    def test_close(self, client, mocker):
        """Test client close."""
        mock_close = mocker.patch.object(client.client, "close")
        client.close()
        mock_close.assert_called_once()
