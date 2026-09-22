"""
Unit tests for dashboard jobs service.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from api import JOBS
from schemas.jobs import Job, JobFilters, JobListResponse

from dashboard.services.jobs_service import JobsService


class TestJobsService:
    """Test suite for jobs service."""

    @pytest.fixture
    def mock_api_client(self):
        """Mock API client."""
        mock = Mock()
        mock.get.return_value = {
            "data": [
                {
                    "id": "1",
                    "title": "Python Developer",
                    "company_name": "TechCorp",
                    "location": "San Francisco",
                    "salary_min": 100000.0,
                    "salary_max": 150000.0,
                    "salary_currency": "USD",
                    "posted_date": datetime.now().isoformat(),
                    "source_site": "LinkedIn",
                    "is_active": True,
                }
            ],
            "total": 1,
            "page": 1,
            "limit": 20,
        }
        return mock

    @pytest.fixture
    def service(self, mock_api_client):
        """Create service instance."""
        return JobsService(api_client=mock_api_client, cache_manager=None)

    def test_fetch_jobs_success(self, service, mock_api_client):
        """Test fetching jobs successfully."""
        filters = JobFilters()

        raw_response = {
            "data": [
                {
                    "id": "1",
                    "title": "Python Developer",
                    "company_name": "TechCorp",
                    "location": "San Francisco",
                    "salary_min": 100000.0,
                    "salary_max": 150000.0,
                    "salary_currency": "USD",
                    "posted_date": datetime.now().isoformat(),
                    "source_site": "LinkedIn",
                    "is_active": True,
                }
            ],
            "total": 1,
            "page": 1,
            "limit": 20,
        }

        with patch.object(service, "_fetch_jobs_cached", return_value=raw_response):
            response = service.fetch_jobs(filters, page=1, page_size=20)

        assert isinstance(response, JobListResponse)
        assert len(response.items) == 1
        assert response.total == 1
        assert response.page == 1
        assert response.page_size == 20
        assert response.total_pages == 1

        job = response.items[0]
        assert isinstance(job, Job)
        assert job.title == "Python Developer"
        assert job.company_name == "TechCorp"

    def test_fetch_jobs_with_filters(self, service, mock_api_client):
        """Test fetching jobs with filters."""
        filters = JobFilters(
            search="Python",
            company="TechCorp",
            location="San Francisco",
            min_salary=100000.0,
            max_salary=150000.0,
        )

        raw_response = {
            "data": [],
            "total": 0,
            "page": 1,
            "limit": 20,
        }
        with patch.object(
            service,
            "_fetch_jobs_cached",
            return_value=raw_response,
        ) as mock_fetch:
            service.fetch_jobs(filters, page=1, page_size=20)

        mock_fetch.assert_called_once()

        args, _ = mock_fetch.call_args

        params = args[1]

        assert params["q"] == "Python"
        assert params["company_name"] == "TechCorp"
        assert params["location"] == "San Francisco"
        assert params["min_salary"] == 100000.0
        assert params["max_salary"] == 150000.0

    def test_fetch_job_success(self, service, mock_api_client):
        """Test fetching a single job successfully."""
        mock_api_client.get.return_value = {
            "id": "1",
            "title": "Python Developer",
            "company_name": "TechCorp",
            "location": "San Francisco",
            "salary_min": 100000.0,
            "salary_max": 150000.0,
            "salary_currency": "USD",
            "posted_date": datetime.now().isoformat(),
            "source_site": "LinkedIn",
            "is_active": True,
        }

        job = service.fetch_job("1")

        assert isinstance(job, Job)
        assert job.id == "1"
        assert job.title == "Python Developer"

    def test_fetch_job_not_found(self, service, mock_api_client):
        """Test fetching a job that doesn't exist."""
        mock_api_client.get.side_effect = Exception("Not Found")

        job = service.fetch_job("999")
        assert job is None

    def test_build_params_with_filters(self, service):
        """Test building API parameters from filters."""
        filters = JobFilters(
            search="Python",
            company="TechCorp",
            location="San Francisco",
            source_site="adzuna",
            min_salary=100000.0,
            max_salary=150000.0,
        )

        params = service._build_params(filters, page=1, page_size=20)

        assert params["page"] == 1
        assert params["limit"] == 20
        assert params["q"] == "Python"
        assert params["company_name"] == "TechCorp"
        assert params["location"] == "San Francisco"
        assert params["source_site"] == "adzuna"
        assert params["min_salary"] == 100000.0
        assert params["max_salary"] == 150000.0

    def test_build_params_empty_filters(self, service):
        """Test building API parameters with empty filters."""
        filters = JobFilters()
        params = service._build_params(filters, page=1, page_size=20)

        assert params["page"] == 1
        assert params["limit"] == 20
        assert "q" not in params
        assert "company_name" not in params
        assert "location" not in params

    def test_normalize_job(self, service):
        """Test normalizing a raw job dict."""
        raw = {
            "id": "1",
            "title": "Python Developer",
            "company_name": "TechCorp",
            "location": "San Francisco",
            "description": "Test description",
            "salary_min": 100000.0,
            "salary_max": 150000.0,
            "salary_currency": "USD",
            "posted_date": datetime.now().isoformat(),
            "source_site": "LinkedIn",
            "source_url": "https://example.com",
            "is_active": True,
        }

        job = service._normalize_job(raw)

        assert isinstance(job, Job)
        assert job.id == "1"
        assert job.title == "Python Developer"
        assert job.company_name == "TechCorp"
        assert job.location == "San Francisco"
        assert job.salary_min == 100000.0
        assert job.salary_max == 150000.0
        assert job.is_active is True

    def test_normalize_job_missing_fields(self, service):
        """Test normalizing a job with missing fields."""
        raw = {"id": "1", "title": "Python Developer"}

        job = service._normalize_job(raw)

        assert job.id == "1"
        assert job.title == "Python Developer"
        assert job.company_name == ""
        assert job.location == ""
        assert job.salary_min is None
        assert job.salary_max is None
        assert job.salary_currency == "USD"
        assert job.is_active is True

    def test_calc_total_pages(self, service):
        """Test total pages calculation."""
        assert service._calc_total_pages(100, 20) == 5
        assert service._calc_total_pages(95, 20) == 5
        assert service._calc_total_pages(20, 20) == 1
        assert service._calc_total_pages(0, 20) == 1
        assert service._calc_total_pages(100, 0) == 1

    def test_refresh(self, service, mock_api_client):
        """Test refreshing service."""
        service.refresh()
        # Should not raise errors

    def test_build_params_with_language_and_tech_role(self, service):
        """Test building parameters for language and tech-role filters."""
        filters = JobFilters(
            language="en",
            is_tech_role=True,
        )

        params = service._build_params(filters, page=2, page_size=10)

        assert params["page"] == 2
        assert params["limit"] == 10
        assert params["language"] == "en"
        assert params["is_tech_role"] is True

    def test_parse_datetime_with_datetime_value(self, service):
        """Test that an existing datetime is returned unchanged."""
        value = datetime(2026, 9, 19, 12, 30)

        result = service._parse_datetime(value)

        assert result is value

    def test_parse_datetime_with_fallback_parser(self, service):
        """Test fallback parsing when ISO parsing fails."""
        result = service._parse_datetime("September 19, 2026 12:30 PM")

        assert result.year == 2026
        assert result.month == 9
        assert result.day == 19
        assert result.hour == 12
        assert result.minute == 30

    def test_parse_datetime_with_invalid_value(self, service):
        """Test fallback to current time when parsing fails."""
        before = datetime.now()

        result = service._parse_datetime("not-a-valid-date")

        after = datetime.now()

        assert before <= result <= after

    def test_fetch_jobs_cached_success(self):
        """Test the cached jobs API call."""
        expected = {
            "data": [],
            "total": 0,
            "page": 1,
            "limit": 20,
        }

        mock_client = Mock()
        mock_client.get.return_value = expected

        with patch("api.client.APIClient", return_value=mock_client):
            result = getattr(JobsService._fetch_jobs_cached, "__wrapped__")(
                "https://example.com",
                {"page": 1, "limit": 20},
            )

        assert result == expected
        mock_client.get.assert_called_once_with(
            JOBS,
            params={"page": 1, "limit": 20},
        )

    def test_fetch_jobs_cached_reraises_api_error(self):
        """Test that cached API errors are logged and re-raised."""
        mock_client = Mock()
        mock_client.get.side_effect = RuntimeError("API error")

        with patch("api.client.APIClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="API error"):
                getattr(JobsService._fetch_jobs_cached, "__wrapped__")(
                    "https://example.com",
                    {"page": 1, "limit": 20},
                )
