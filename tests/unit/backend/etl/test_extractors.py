"""
Unit tests for ETL extractors.
"""

from unittest.mock import Mock

import pytest

from app.etl.clients.http_client import HTTPClient
from app.etl.extractors.jobs_api import (
    RAW_SOURCE_COUNTRY_FIELD,
    JobsExtractor,
    mask_params,
    mask_sensitive,
)


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


class TestJobsExtractorCoverage:
    """Additional coverage tests for jobs_api.py."""

    @pytest.fixture
    def client(self):
        """Create a mocked HTTP client."""
        return Mock()

    @pytest.fixture
    def extractor(self, client):
        """Create an extractor with an injected client."""
        return JobsExtractor(
            api_url="https://api.test.com",
            app_id="test_app_id",
            api_key="test_api_key",
            debug=False,
            results_per_page=2,
            max_pages=3,
            client=client,
        )

    @pytest.fixture
    def jobs(self):
        """Create sample jobs."""
        return [
            {"id": "1", "title": "Python Developer"},
            {"id": "2", "title": "Data Engineer"},
        ]

    def test_mask_sensitive_short_string(self):
        """Strings at or below the show length are fully masked."""
        assert mask_sensitive("abc") == "***"
        assert mask_sensitive("abcd") == "****"

    def test_mask_sensitive_long_string(self):
        """Long strings expose only the configured prefix."""
        assert mask_sensitive("secret123") == "secr..."
        assert mask_sensitive("secret123", show=2) == "se..."

    def test_mask_sensitive_empty_string(self):
        """Empty values are represented as None."""
        assert mask_sensitive("") == "None"

    def test_mask_params_none_and_empty(self):
        """Empty parameter collections return empty dictionaries."""
        assert mask_params(None) == {}
        assert mask_params({}) == {}

    def test_mask_params_masks_sensitive_keys(self):
        """Sensitive keys are masked."""
        params = {
            "app_id": "test123456",
            "app_key": "secret456",
            "api_key": "apikey123",
            "key": "key123",
            "id": "identifier",
            "secret": "secretvalue",
            "password": "password123",
            "token": "token123",
        }

        masked = mask_params(params)

        assert masked["app_id"] == "test..."
        assert masked["app_key"] == "secr..."
        assert masked["api_key"] == "apik..."
        assert masked["key"] == "key1..."
        assert masked["id"] == "iden..."
        assert masked["secret"] == "secr..."
        assert masked["password"] == "pass..."
        assert masked["token"] == "toke..."

    def test_mask_params_masks_sensitive_substrings_case_insensitively(self):
        """Keys containing sensitive words are also masked."""
        params = {
            "MY_API_KEY_VALUE": "abcdefgh",
            "client_password_hash": "12345678",
            "AuthTokenValue": "abcdefgh",
            "normal": 123,
        }

        masked = mask_params(params)

        assert masked["MY_API_KEY_VALUE"] == "abcd..."
        assert masked["client_password_hash"] == "1234..."
        assert masked["AuthTokenValue"] == "abcd..."
        assert masked["normal"] == "123"

    def test_extract_missing_credentials(self, client):
        """Extraction stops immediately when credentials are missing."""
        extractor = JobsExtractor(
            api_url="https://api.test.com",
            app_id="",
            api_key="test_key",
            client=client,
        )

        assert extractor.extract("us") == []
        client.get.assert_not_called()

    def test_extract_single_page(self, extractor, client, jobs):
        """Extraction attaches country metadata and returns jobs."""
        client.get.return_value = {
            "results": jobs,
            "count": 2,
        }

        result = extractor.extract("us")

        assert result == jobs
        assert all(job[RAW_SOURCE_COUNTRY_FIELD] == "us" for job in result)
        client.get.assert_called_once()

    def test_extract_multiple_pages(self, extractor, client):
        """Extraction continues while more pages are available."""
        page_one = [
            {"id": "1"},
            {"id": "2"},
        ]
        page_two = [
            {"id": "3"},
            {"id": "4"},
        ]

        client.get.side_effect = [
            {"results": page_one, "count": 6},
            {"results": page_two, "count": 6},
            {"results": [], "count": 6},
        ]

        result = extractor.extract("de")

        assert len(result) == 4
        assert all(job[RAW_SOURCE_COUNTRY_FIELD] == "de" for job in result)
        assert client.get.call_count == 3

    def test_extract_stops_when_has_more_is_false(self, extractor, client, jobs):
        """Extraction stops when the API reports no additional pages."""
        client.get.return_value = {
            "results": jobs,
            "count": 2,
        }

        result = extractor.extract("gb")

        assert len(result) == 2
        assert client.get.call_count == 1

    def test_extract_stops_when_page_is_shorter_than_page_size(
        self, extractor, client
    ):
        """Extraction stops when fewer than the requested page size are returned."""
        client.get.return_value = {
            "results": [{"id": "1"}],
            "count": 100,
        }

        result = extractor.extract("gb")

        assert len(result) == 1
        assert client.get.call_count == 1

    def test_extract_handles_exception(self, extractor, client, mocker):
            """Unexpected extraction errors are logged and accumulated jobs returned."""
            mock_exception = mocker.patch(
                "app.etl.extractors.jobs_api.logger.exception"
            )

            client.get.side_effect = [
                {
                    "results": [{"id": "1"}, {"id": "2"}],
                    "count": 100,
                },
                Exception("API failure"),
            ]

            result = extractor.extract("us")

            assert len(result) == 2
            assert all(job[RAW_SOURCE_COUNTRY_FIELD] == "us" for job in result)
            assert client.get.call_count == 2
            mock_exception.assert_called_once_with(
                "Unexpected error fetching jobs for %s",
                "us",
            )

    def test_extract_handles_exception(self, extractor, client, mocker):
        """Unexpected extraction errors are logged and accumulated jobs returned."""
        mock_exception = mocker.patch(
            "app.etl.extractors.jobs_api.logger.exception"
        )

        client.get.side_effect = [
            {
                "results": [{"id": "1"}, {"id": "2"}],
                "count": 100,
            },
            Exception("API failure"),
        ]

        result = extractor.extract("us")

        assert len(result) == 2
        assert all(job[RAW_SOURCE_COUNTRY_FIELD] == "us" for job in result)
        assert client.get.call_count == 2
        mock_exception.assert_called_once_with(
            "Unexpected error fetching jobs for %s",
            "us",
        )

    def test_extract_with_params_missing_credentials(self, client):
        """Parameterized extraction stops when credentials are missing."""
        extractor = JobsExtractor(
            api_url="https://api.test.com",
            app_id="test_app_id",
            api_key="",
            client=client,
        )

        assert extractor.extract_with_params("us", {"what": "python"}) == []
        client.get.assert_not_called()

    def test_extract_with_params_defaults_search_params_to_empty_dict(
        self, extractor, client
    ):
        """None search parameters are converted to an empty dictionary."""
        client.get.return_value = {
            "results": [{"id": "1"}],
            "count": 1,
        }

        result = extractor.extract_with_params("gb")

        assert len(result) == 1
        assert result[0][RAW_SOURCE_COUNTRY_FIELD] == "gb"

        params = client.get.call_args.kwargs["params"]
        assert params["app_id"] == "test_app_id"
        assert params["app_key"] == "test_api_key"
        assert params["results_per_page"] == 2

    def test_extract_with_params_applies_search_params(
        self, extractor, client
    ):
        """Custom search parameters are passed to the API."""
        client.get.return_value = {
            "results": [{"id": "1"}],
            "count": 1,
        }

        result = extractor.extract_with_params(
            "us",
            {
                "what": "python developer",
                "where": "New York",
            },
        )

        assert len(result) == 1

        params = client.get.call_args.kwargs["params"]
        assert params["what"] == "python developer"
        assert params["where"] == "New York"

    def test_extract_with_params_multiple_pages(self, extractor, client):
        """Parameterized extraction supports multiple pages."""
        client.get.side_effect = [
            {
                "results": [{"id": "1"}, {"id": "2"}],
                "count": 6,
            },
            {
                "results": [{"id": "3"}, {"id": "4"}],
                "count": 6,
            },
            {
                "results": [{"id": "5"}, {"id": "6"}],
                "count": 6,
            },
        ]

        result = extractor.extract_with_params(
            "de",
            {"what": "software engineer"},
        )

        assert len(result) == 6
        assert all(job[RAW_SOURCE_COUNTRY_FIELD] == "de" for job in result)
        assert client.get.call_count == 3

    def test_extract_with_params_stops_when_page_is_short(
        self, extractor, client
    ):
        """Parameterized extraction stops when a short page is returned."""
        client.get.return_value = {
            "results": [{"id": "1"}],
            "count": 100,
        }

        result = extractor.extract_with_params(
            "gb",
            {"what": "python"},
        )

        assert len(result) == 1
        assert client.get.call_count == 1

    def test_extract_with_params_handles_exception(
        self, extractor, client, mocker
    ):
        """Parameterized extraction logs unexpected errors."""
        mock_exception = mocker.patch(
            "app.etl.extractors.jobs_api.logger.exception"
        )

        client.get.side_effect = Exception("API failure")

        result = extractor.extract_with_params(
            "us",
            {"what": "python"},
        )

        assert result == []
        mock_exception.assert_called_once_with(
            "Unexpected error fetching jobs for %s with params %s",
            "us",
            {"what": "python"},
        )

    def test_private_fetch_page_invalid_results_type(
        self, extractor, client
    ):
        """Invalid API results are treated as an empty page."""
        client.get.return_value = {
            "results": {"not": "a list"},
            "count": 100,
        }

        jobs, has_more = extractor._fetch_page("gb", 1)

        assert jobs == []
        assert has_more is False

    def test_private_fetch_page_invalid_count(
        self, extractor, client
    ):
        """Invalid count values are treated as zero."""
        client.get.return_value = {
            "results": [{"id": "1"}],
            "count": "not-an-int",
        }

        jobs, has_more = extractor._fetch_page("gb", 1)

        assert jobs == [{"id": "1"}]
        assert has_more is False

    def test_private_fetch_page_has_more(
        self, extractor, client
    ):
        """has_more is true when additional pages exist."""
        client.get.return_value = {
            "results": [{"id": "1"}, {"id": "2"}],
            "count": 10,
        }

        jobs, has_more = extractor._fetch_page("gb", 1)

        assert len(jobs) == 2
        assert has_more is True

    def test_private_fetch_page_debug_logging(
        self, extractor, client, caplog
    ):
        """Private page fetching executes debug logging."""
        extractor.debug = True
        client.get.return_value = {
            "results": [],
            "count": 0,
        }

        with caplog.at_level("DEBUG"):
            extractor._fetch_page("gb", 1)

        assert "URL:" in caplog.text
        assert "Params:" in caplog.text

    def test_fetch_page_with_params_invalid_results_type(
        self, extractor, client
    ):
        """Parameterized page fetching handles invalid results."""
        client.get.return_value = {
            "results": {"invalid": True},
            "count": 100,
        }

        jobs, has_more = extractor._fetch_page_with_params(
            "gb",
            1,
            {"what": "python"},
        )

        assert jobs == []
        assert has_more is False

    def test_fetch_page_with_params_invalid_count(
        self, extractor, client
    ):
        """Parameterized page fetching handles invalid counts."""
        client.get.return_value = {
            "results": [{"id": "1"}],
            "count": "invalid",
        }

        jobs, has_more = extractor._fetch_page_with_params(
            "gb",
            1,
            {"what": "python"},
        )

        assert jobs == [{"id": "1"}]
        assert has_more is False

    def test_fetch_page_with_params_merges_params(
        self, extractor, client
    ):
        """Custom parameters are merged into the base API parameters."""
        client.get.return_value = {
            "results": [],
            "count": 0,
        }

        extractor._fetch_page_with_params(
            "us",
            2,
            {
                "what": "python",
                "where": "London",
            },
        )

        params = client.get.call_args.kwargs["params"]

        assert params["app_id"] == "test_app_id"
        assert params["app_key"] == "test_api_key"
        assert params["results_per_page"] == 2
        assert params["what"] == "python"
        assert params["where"] == "London"

    def test_fetch_page_with_params_can_override_page_size(
        self, extractor, client
    ):
        """Search parameters can override the default page size."""
        client.get.return_value = {
            "results": [],
            "count": 0,
        }

        extractor._fetch_page_with_params(
            "us",
            1,
            {"results_per_page": 50},
        )

        params = client.get.call_args.kwargs["params"]
        assert params["results_per_page"] == 50

    def test_fetch_page_with_params_has_more(
        self, extractor, client
    ):
        """Parameterized page fetching detects additional pages."""
        client.get.return_value = {
            "results": [{"id": "1"}, {"id": "2"}],
            "count": 10,
        }

        jobs, has_more = extractor._fetch_page_with_params(
            "gb",
            1,
            {"what": "python"},
        )

        assert len(jobs) == 2
        assert has_more is True

    def test_fetch_page_with_params_debug_logging(
        self, extractor, client, caplog
    ):
        """Parameterized page fetching executes debug logging."""
        extractor.debug = True
        client.get.return_value = {
            "results": [],
            "count": 0,
        }

        with caplog.at_level("DEBUG"):
            extractor._fetch_page_with_params(
                "gb",
                1,
                {"what": "python"},
            )

        assert "URL:" in caplog.text
        assert "Params:" in caplog.text

    def test_fetch_page_uses_default_results_per_page(
        self, extractor, client
    ):
        """fetch_page uses the extractor page size when no override is supplied."""
        client.get.return_value = {"results": [], "count": 0}

        extractor.fetch_page(page=2, country="us")

        params = client.get.call_args.kwargs["params"]
        assert params["results_per_page"] == 2
        assert client.get.call_args.args[0] == (
            "https://api.test.com/jobs/us/search/2"
        )

    def test_fetch_page_debug_logging(self, extractor, client, caplog):
        """fetch_page executes its debug logging branch."""
        extractor.debug = True
        client.get.return_value = {"results": [], "count": 0}

        with caplog.at_level("DEBUG"):
            extractor.fetch_page(page=1, country="us")

        assert "URL:" in caplog.text
        assert "Params:" in caplog.text

    def test_fetch_page_debug_masks_credentials(
        self, extractor, client, caplog
    ):
        """Debug logging does not expose API credentials."""
        extractor.debug = True
        client.get.return_value = {"results": [], "count": 0}

        with caplog.at_level("DEBUG"):
            extractor.fetch_page(page=1)

        assert "test_app_id" not in caplog.text
        assert "test_api_key" not in caplog.text
        assert "test..." in caplog.text

    def test_private_fetch_page_invalid_results_type(
        self, extractor, client
    ):
        """Invalid API results are treated as an empty page."""
        client.get.return_value = {
            "results": {"not": "a list"},
            "count": 100,
        }

        jobs, has_more = extractor._fetch_page("gb", 1)

        assert jobs == []
        assert has_more is False

    def test_private_fetch_page_invalid_count(
        self, extractor, client
    ):
        """Invalid count values are treated as zero."""
        client.get.return_value = {
            "results": [{"id": "1"}],
            "count": "not-an-int",
        }

        jobs, has_more = extractor._fetch_page("gb", 1)

        assert jobs == [{"id": "1"}]
        assert has_more is False

    def test_private_fetch_page_has_more(
        self, extractor, client
    ):
        """has_more is true when additional pages exist."""
        client.get.return_value = {
            "results": [{"id": "1"}, {"id": "2"}],
            "count": 10,
        }

        jobs, has_more = extractor._fetch_page("gb", 1)

        assert len(jobs) == 2
        assert has_more is True

    def test_private_fetch_page_debug_logging(
        self, extractor, client, caplog
    ):
        """Private page fetching executes debug logging."""
        extractor.debug = True
        client.get.return_value = {
            "results": [],
            "count": 0,
        }

        with caplog.at_level("DEBUG"):
            extractor._fetch_page("gb", 1)

        assert "URL:" in caplog.text
        assert "Params:" in caplog.text

    def test_fetch_page_with_params_invalid_results_type(
        self, extractor, client
    ):
        """Parameterized page fetching handles invalid results."""
        client.get.return_value = {
            "results": {"invalid": True},
            "count": 100,
        }

        jobs, has_more = extractor._fetch_page_with_params(
            "gb",
            1,
            {"what": "python"},
        )

        assert jobs == []
        assert has_more is False

    def test_fetch_page_with_params_invalid_count(
        self, extractor, client
    ):
        """Parameterized page fetching handles invalid counts."""
        client.get.return_value = {
            "results": [{"id": "1"}],
            "count": "invalid",
        }

        jobs, has_more = extractor._fetch_page_with_params(
            "gb",
            1,
            {"what": "python"},
        )

        assert jobs == [{"id": "1"}]
        assert has_more is False

    def test_fetch_page_with_params_merges_params(
        self, extractor, client
    ):
        """Custom parameters are merged into the base API parameters."""
        client.get.return_value = {
            "results": [],
            "count": 0,
        }

        extractor._fetch_page_with_params(
            "us",
            2,
            {
                "what": "python",
                "where": "London",
            },
        )

        params = client.get.call_args.kwargs["params"]

        assert params["app_id"] == "test_app_id"
        assert params["app_key"] == "test_api_key"
        assert params["results_per_page"] == 2
        assert params["what"] == "python"
        assert params["where"] == "London"

    def test_fetch_page_with_params_can_override_page_size(
        self, extractor, client
    ):
        """Search parameters can override the default page size."""
        client.get.return_value = {
            "results": [],
            "count": 0,
        }

        extractor._fetch_page_with_params(
            "us",
            1,
            {"results_per_page": 50},
        )

        params = client.get.call_args.kwargs["params"]
        assert params["results_per_page"] == 50

    def test_fetch_page_with_params_debug_logging(
        self, extractor, client, caplog
    ):
        """Parameterized page fetching executes debug logging."""
        extractor.debug = True
        client.get.return_value = {
            "results": [],
            "count": 0,
        }

        with caplog.at_level("DEBUG"):
            extractor._fetch_page_with_params(
                "gb",
                1,
                {"what": "python"},
            )

        assert "URL:" in caplog.text
        assert "Params:" in caplog.text