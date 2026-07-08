"""
Unit tests for ETL extractors.
"""

from unittest.mock import Mock

import pytest

from app.etl.clients.http_client import HTTPClient
from app.etl.extractors.jobs_api import JobsExtractor


class TestJobsExtractor:
    """Test suite for JobsExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create a JobsExtractor instance."""
        return JobsExtractor(
            api_url="https://api.test.com",
            app_id="test_app_id",
            api_key="test_api_key",
            debug=False,
        )

    @pytest.fixture
    def mock_response(self):
        """Mock API response."""
        return {
            "results": [
                {
                    "id": "job_123",
                    "title": "Python Developer",
                    "company": {"display_name": "TechCorp"},
                    "location": {"display_name": "San Francisco"},
                    "description": "Test description",
                    "salary": {"min": 100000, "max": 150000, "currency": "USD"},
                    "redirect_url": "https://example.com/job/123",
                    "created": "2026-01-15T10:30:00Z",
                }
            ],
            "count": 1,
        }

    def test_init(self, extractor):
        """Test initialization."""
        assert extractor.api_url == "https://api.test.com"
        assert extractor.app_id == "test_app_id"
        assert extractor.api_key == "test_api_key"
        assert extractor.debug is False
        assert isinstance(extractor.client, HTTPClient)

    def test_fetch_page_success(self, extractor, mock_response, mocker):
        """Test successful page fetch."""
        mock_get = mocker.patch.object(extractor.client, "get")
        mock_get.return_value = mock_response

        result = extractor.fetch_page(page=1, results_per_page=10)

        assert result == mock_response
        mock_get.assert_called_once()

    def test_fetch_page_url_construction(self, extractor, mock_response, mocker):
        """Test URL construction for different pages."""
        mock_get = mocker.patch.object(extractor.client, "get")
        mock_get.return_value = mock_response

        # Page 1
        extractor.fetch_page(page=1)
        call_args = mock_get.call_args
        assert "jobs/gb/search/1" in call_args[0][0]

        # Page 2
        extractor.fetch_page(page=2)
        call_args = mock_get.call_args
        assert "jobs/gb/search/2" in call_args[0][0]

    def test_fetch_page_params(self, extractor, mock_response, mocker):
        """Test that correct params are passed."""
        mock_get = mocker.patch.object(extractor.client, "get")
        mock_get.return_value = mock_response

        extractor.fetch_page(page=1, results_per_page=25)

        call_args = mock_get.call_args
        params = call_args[1]["params"]
        assert params["app_id"] == "test_app_id"
        assert params["app_key"] == "test_api_key"
        assert params["results_per_page"] == 25

    def test_fetch_page_with_debug(self, mock_response, mocker):
        """Test fetch page with debug enabled."""
        extractor = JobsExtractor(
            api_url="https://api.test.com", app_id="test_app_id", api_key="test_api_key", debug=True
        )
        mock_get = mocker.patch.object(extractor.client, "get")
        mock_get.return_value = mock_response

        # Should not raise any errors
        result = extractor.fetch_page(page=1)
        assert result == mock_response

    def test_fetch_page_http_error(self, extractor, mocker):
        """Test HTTP error handling."""
        mock_get = mocker.patch.object(extractor.client, "get")
        mock_get.side_effect = Exception("HTTP 500 Error")

        with pytest.raises(Exception) as exc_info:
            extractor.fetch_page(page=1)

        assert "HTTP 500 Error" in str(exc_info.value)


class TestHTTPClient:
    """Test suite for HTTPClient."""

    @pytest.fixture
    def client(self):
        """Create an HTTPClient instance."""
        return HTTPClient(timeout=30, debug=False)

    def test_init(self, client):
        """Test initialization."""
        assert client.timeout == 30
        assert client.debug is False
        assert client.session is not None
        assert client.session.headers.get("Accept") == "application/json"

    def test_get_success(self, client, mocker):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": "test"}
        mock_response.url = "https://api.test.com"
        mock_response.status_code = 200

        mock_session_get = mocker.patch.object(client.session, "get")
        mock_session_get.return_value = mock_response

        result = client.get("https://api.test.com", params={"key": "value"})

        assert result == {"data": "test"}
        mock_session_get.assert_called_once_with(
            "https://api.test.com", params={"key": "value"}, timeout=30
        )

    def test_get_http_error(self, client, mocker):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.url = "https://api.test.com"
        mock_response.text = "Not Found"
        mock_response.request.headers = {}
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")

        mock_session_get = mocker.patch.object(client.session, "get")
        mock_session_get.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            client.get("https://api.test.com")

        assert "404 Not Found" in str(exc_info.value)

    def test_get_with_debug(self, mocker):
        """Test GET request with debug enabled."""
        client = HTTPClient(debug=True)

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": "test"}
        mock_response.url = "https://api.test.com"
        mock_response.status_code = 200

        mock_session_get = mocker.patch.object(client.session, "get")
        mock_session_get.return_value = mock_response

        # Should not raise any errors
        result = client.get("https://api.test.com")
        assert result == {"data": "test"}

    def test_mask_sensitive_with_string(self):
        """Test sensitive data masking with string."""
        from app.etl.clients.http_client import mask_sensitive

        assert mask_sensitive("secret123") == "secr..."
        assert mask_sensitive("abc") == "***"
        assert mask_sensitive("") == "None"

    def test_mask_sensitive_with_none(self):
        """Test sensitive data masking with None."""
        from app.etl.clients.http_client import mask_sensitive

        # Passing None should return "None"
        assert mask_sensitive("") == "None"

    def test_mask_params(self):
        """Test parameter masking."""
        from app.etl.clients.http_client import mask_params

        params = {"app_id": "test123", "app_key": "secret456", "normal_param": "visible"}
        masked = mask_params(params)

        assert masked["app_id"] == "test..."  # Masked
        assert masked["app_key"] == "secr..."  # Masked
        assert masked["normal_param"] == "visible"  # Visible

    def test_mask_params_empty(self):
        """Test masking empty params."""
        from app.etl.clients.http_client import mask_params

        assert mask_params(None) == {}
        assert mask_params({}) == {}
