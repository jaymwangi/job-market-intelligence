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

    def test_http_error_with_invalid_json(self, client, mocker):
        """Test HTTP error handling when response JSON is invalid."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400", request=Mock(), response=mock_response
        )

        mock_request = mocker.patch.object(client.client, "request")
        mock_request.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            client.get("/test")

        assert "Request failed: 400 - Bad Request" in str(exc_info.value)

    def test_generic_http_error(self, client, mocker):
        """Test generic HTTP error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.json.return_value = {}

        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=Mock(), response=mock_response
        )

        mock_request = mocker.patch.object(client.client, "request")
        mock_request.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            client.get("/test")

        assert "Request failed: 401 - Unauthorized" in str(exc_info.value)

    def test_get_jobs_with_all_filters(self, client, mocker):
        """Test get_jobs includes all provided filters."""
        mock_get = mocker.patch.object(client, "get", return_value={"data": []})

        result = client.get_jobs(
            page=2,
            limit=50,
            q="python",
            company_name="Acme",
            location="Nairobi",
            source_site="linkedin",
            min_salary=50000,
            max_salary=150000,
            country_code="KE",
            technology_category="backend",
            employment_type="full-time",
            is_tech_role=True,
            language="en",
        )

        assert result == {"data": []}
        mock_get.assert_called_once_with(
            "api/v1/jobs",
            params={
                "page": 2,
                "limit": 50,
                "q": "python",
                "company_name": "Acme",
                "location": "Nairobi",
                "source_site": "linkedin",
                "min_salary": 50000,
                "max_salary": 150000,
                "country_code": "KE",
                "technology_category": "backend",
                "employment_type": "full-time",
                "is_tech_role": "true",
                "language": "en",
            },
        )

    def test_translate_job(self, client, mocker):
        """Test translate_job constructs the correct URL."""
        mock_post = mocker.patch.object(client, "post", return_value={"translated": True})

        result = client.translate_job("job-123", target_language="fr")

        assert result == {"translated": True}
        mock_post.assert_called_once_with("api/v1/jobs/job-123/translate?target_language=fr")

    def test_unexpected_error(self, client, mocker):
        """Test unexpected exception handling."""
        mock_request = mocker.patch.object(client.client, "request")
        mock_request.side_effect = RuntimeError("Unexpected failure")

        with pytest.raises(APIError) as exc_info:
            client.get("/test")

        assert "Unexpected error: Unexpected failure" in str(exc_info.value)

    @pytest.mark.parametrize(
        ("method_name", "expected_path"),
        [
            ("health", "api/v1/health"),
            ("live", "api/v1/health/live"),
            ("ready", "api/v1/health/ready"),
            ("get_job", "api/v1/jobs/job-123"),
            ("get_salary_statistics", "api/v1/analytics/salary-statistics"),
            ("get_salary_distribution", "api/v1/analytics/salary-distribution"),
            ("get_employment_types", "api/v1/analytics/employment-types"),
            ("get_dataset_summary", "api/v1/analytics/dataset-summary"),
            ("get_overview", "api/v1/analytics/overview"),
            ("get_dashboard_summary", "api/v1/analytics/dashboard-summary"),
            ("get_language_distribution", "api/v1/analytics/language/distribution"),
            ("get_language_by_country", "api/v1/analytics/language/by-country"),
            (
                "get_english_vs_non_english",
                "api/v1/analytics/language/english-vs-non-english",
            ),
            ("get_language_salary_stats", "api/v1/analytics/language/salary"),
            ("get_tech_vs_non_tech", "api/v1/analytics/tech/vs-non-tech"),
            (
                "get_tech_category_distribution",
                "api/v1/analytics/tech/category-distribution",
            ),
            ("get_tech_by_country", "api/v1/analytics/tech/by-country"),
            ("get_tech_salary_stats", "api/v1/analytics/tech/salary"),
            ("get_enriched_countries", "api/v1/analytics/enriched/countries"),
            ("get_enriched_technology", "api/v1/analytics/enriched/technology"),
        ],
    )
    def test_simple_get_wrappers(self, client, mocker, method_name, expected_path):
        """Test API methods that directly delegate to GET."""
        mock_get = mocker.patch.object(client, "get", return_value={"data": "test"})

        if method_name == "get_job":
            result = getattr(client, method_name)("job-123")
        else:
            result = getattr(client, method_name)()

        assert result == {"data": "test"}
        mock_get.assert_called_once_with(expected_path)

    def test_get_enriched_skills_with_filters(self, client, mocker):
        """Test enriched skills with country and tech filters."""
        mock_get = mocker.patch.object(client, "get", return_value={"data": "test"})

        result = client.get_enriched_skills(
            limit=30,
            country_code="KE",
            tech_only=True,
        )

        assert result == {"data": "test"}
        mock_get.assert_called_once_with(
            "api/v1/analytics/enriched/skills",
            params={
                "limit": 30,
                "country_code": "KE",
                "tech_only": "true",
            },
        )

    def test_get_enriched_salary_with_filters(self, client, mocker):
        """Test enriched salary with country and tech filters."""
        mock_get = mocker.patch.object(client, "get", return_value={"data": "test"})

        result = client.get_enriched_salary(
            country_code="KE",
            tech_only=True,
        )

        assert result == {"data": "test"}
        mock_get.assert_called_once_with(
            "api/v1/analytics/enriched/salary",
            params={
                "country_code": "KE",
                "tech_only": "true",
            },
        )

    @pytest.mark.parametrize(
        ("method_name", "args", "expected_path", "expected_params"),
        [
            ("get_top_skills", (25,), "api/v1/analytics/top-skills", {"limit": 25}),
            ("get_top_companies", (25,), "api/v1/analytics/top-companies", {"limit": 25}),
            ("get_jobs_by_location", (25,), "api/v1/analytics/jobs-by-location", {"limit": 25}),
            ("get_salary_by_location", (25,), "api/v1/analytics/salary-by-location", {"limit": 25}),
            ("get_salary_by_company", (25,), "api/v1/analytics/salary-by-company", {"limit": 25}),
            ("get_posting_trend", (60,), "api/v1/analytics/posting-trend", {"days": 60}),
            ("get_recent_jobs", (14,), "api/v1/analytics/recent-jobs", {"days": 14}),
            ("get_tech_skills", (30,), "api/v1/analytics/tech/skills", {"limit": 30}),
        ],
    )
    def test_parameterized_get_wrappers(
        self,
        client,
        mocker,
        method_name,
        args,
        expected_path,
        expected_params,
    ):
        """Test GET methods that pass query parameters."""
        mock_get = mocker.patch.object(client, "get", return_value={"data": "test"})

        result = getattr(client, method_name)(*args)

        assert result == {"data": "test"}
        mock_get.assert_called_once_with(
            expected_path,
            params=expected_params,
        )
