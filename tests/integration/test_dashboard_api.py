"""Integration tests for the dashboard API client.

These tests verify that the dashboard's APIClient can communicate with
the real FastAPI backend and consume the API contracts used by the
dashboard.

The FastAPI database dependency is overridden so all integration tests
use the PostgreSQL test database provided by the ``db_session`` fixture.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import httpx
import pytest

from app.database.session import get_db
from app.main import app
from app.models.job import Job
from dashboard.api.client import APIClient
from dashboard.api.exceptions import (
    APIConnectionError,
    APINotFoundError,
    APIServerError,
    APITimeoutError,
)


class SyncASGITransport(httpx.BaseTransport):
    """Synchronous adapter for httpx.ASGITransport."""

    def __init__(self, app):
        self._transport = httpx.ASGITransport(app=app)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """Execute an ASGI request through a synchronous httpx client."""

        async def send_request() -> httpx.Response:
            return await self._transport.handle_async_request(request)

        async_response = asyncio.run(send_request())

        async def read_body() -> bytes:
            return await async_response.aread()

        content = asyncio.run(read_body())

        headers = dict(async_response.headers)

        # ASGITransport has already decoded the response body.
        # If the original response contained Content-Encoding: gzip,
        # remove the stale header so the synchronous httpx client
        # does not attempt another decompression.
        if headers.get("content-encoding", "").lower() == "gzip":
            headers.pop("content-encoding", None)
            headers["content-length"] = str(len(content))

        return httpx.Response(
            status_code=async_response.status_code,
            headers=headers,
            content=content,
            request=request,
            extensions=async_response.extensions,
        )

    def close(self) -> None:
        """Close the underlying ASGI transport."""

        async def close_transport() -> None:
            await self._transport.aclose()

        asyncio.run(close_transport())


@pytest.fixture
def api_client():
    """Create dashboard API client configured for the test API."""

    client = APIClient(
        base_url="http://testserver",
        timeout=30,
        retries=1,
    )

    yield client
    client.close()


@pytest.fixture
def live_api_client(db_session):
    """Create APIClient backed by the real FastAPI ASGI application.

    The application's database dependency is overridden so all API
    requests use the PostgreSQL test session supplied by the
    ``db_session`` fixture instead of the production database.
    """

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = SyncASGITransport(app)

    client = APIClient(
        base_url="http://testserver",
        timeout=30,
        retries=1,
    )

    client.client.close()

    client.client = httpx.Client(
        transport=transport,
        base_url="http://testserver",
        timeout=30,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        yield client
    finally:
        client.close()
        app.dependency_overrides.clear()


def make_test_job(
    *,
    title: str,
    company_name: str,
    location: str,
    description: str,
    is_tech_role: bool = True,
    technology_category: str | None = "backend",
    source_site: str = "test",
    source_id: str | None = None,
) -> Job:
    """Create a deterministic Job model for dashboard integration tests."""

    return Job(
        id=uuid4(),
        title=title,
        company_name=company_name,
        location=location,
        description=description,
        posted_date=datetime.now(timezone.utc),
        source_url="https://example.com/test-job",
        source_site=source_site,
        source_id=source_id or str(uuid4()),
        is_tech_role=is_tech_role,
        technology_category=technology_category,
        country_code="GB",
        salary_currency="GBP",
        salary_min=50000,
        salary_max=70000,
        language="en",
    )


class TestDashboardAPIHealth:
    """Test dashboard communication with API health endpoints."""

    def test_health(self, live_api_client):
        """Dashboard client can reach the API health endpoint."""
        response = live_api_client.health()

        assert isinstance(response, dict)

    def test_live(self, live_api_client):
        """Dashboard client can reach the liveness endpoint."""
        response = live_api_client.live()

        assert isinstance(response, dict)

    def test_ready(self, live_api_client):
        """Dashboard client can reach the readiness endpoint."""
        response = live_api_client.ready()

        assert isinstance(response, dict)


class TestDashboardAPIJobs:
    """Test dashboard job API integration."""

    def test_get_jobs(self, live_api_client):
        """Dashboard client can retrieve paginated jobs."""
        response = live_api_client.get_jobs()

        assert isinstance(response, dict)

    def test_get_jobs_with_pagination(self, live_api_client):
        """Dashboard client sends pagination parameters correctly."""
        response = live_api_client.get_jobs(
            page=1,
            limit=10,
        )

        assert isinstance(response, dict)

    def test_get_jobs_with_filters(self, live_api_client):
        """Dashboard client sends supported job filters correctly."""
        response = live_api_client.get_jobs(
            page=1,
            limit=10,
            q="python",
            location="London",
            technology_category="backend",
            is_tech_role=True,
        )

        assert isinstance(response, dict)

    def test_search_returns_matching_job(
        self,
        live_api_client,
        db_session,
    ):
        """Search returns the job matching the requested search term."""
        matching_job = make_test_job(
            title="Python Data Engineer",
            company_name="Dashboard Search Co",
            location="London",
            description="Build Python data pipelines.",
        )
        non_matching_job = make_test_job(
            title="Java Developer",
            company_name="Dashboard Other Co",
            location="Manchester",
            description="Build Java applications.",
        )

        db_session.add_all([matching_job, non_matching_job])
        db_session.flush()

        response = live_api_client.get_jobs(
            page=1,
            limit=10,
            q="Python Data Engineer",
        )

        returned_ids = {item["id"] for item in response["data"]}

        assert str(matching_job.id) in returned_ids
        assert str(non_matching_job.id) not in returned_ids
        assert response["total"] == 1

    def test_filters_return_matching_jobs(
        self,
        live_api_client,
        db_session,
    ):
        """Combined filters return only matching jobs."""
        matching_job = make_test_job(
            title="Backend Engineer",
            company_name="Dashboard Filter Co",
            location="London",
            description="Backend Python development.",
            is_tech_role=True,
            technology_category="backend",
        )
        wrong_location = make_test_job(
            title="Backend Engineer",
            company_name="Dashboard Filter Co",
            location="Manchester",
            description="Backend Python development.",
            is_tech_role=True,
            technology_category="backend",
        )
        wrong_category = make_test_job(
            title="Frontend Engineer",
            company_name="Dashboard Filter Co",
            location="London",
            description="Frontend development.",
            is_tech_role=True,
            technology_category="frontend",
        )
        non_tech = make_test_job(
            title="Project Manager",
            company_name="Dashboard Filter Co",
            location="London",
            description="Manage technology projects.",
            is_tech_role=False,
            technology_category=None,
        )

        db_session.add_all(
            [
                matching_job,
                wrong_location,
                wrong_category,
                non_tech,
            ]
        )
        db_session.flush()

        response = live_api_client.get_jobs(
            page=1,
            limit=10,
            location="London",
            technology_category="backend",
            is_tech_role=True,
        )

        returned_ids = {item["id"] for item in response["data"]}

        assert returned_ids == {str(matching_job.id)}
        assert response["total"] == 1

    def test_pagination_returns_requested_page(
        self,
        live_api_client,
        db_session,
    ):
        """Pagination returns the requested page and page size."""
        jobs = [
            make_test_job(
                title=f"Pagination Job {index}",
                company_name="Dashboard Pagination Co",
                location="Nairobi",
                description=f"Pagination test job {index}.",
            )
            for index in range(3)
        ]

        db_session.add_all(jobs)
        db_session.flush()

        response = live_api_client.get_jobs(
            page=2,
            limit=1,
        )

        assert response["page"] == 2
        assert response["limit"] == 1
        assert len(response["data"]) == 1
        assert response["total"] >= 3

    def test_get_job_returns_requested_job(
        self,
        live_api_client,
        db_session,
    ):
        """Dashboard client retrieves an existing job by ID."""
        job = make_test_job(
            title="Specific Dashboard Job",
            company_name="Dashboard Detail Co",
            location="Nairobi",
            description="Specific job for dashboard detail testing.",
        )

        db_session.add(job)
        db_session.flush()

        response = live_api_client.get_job(str(job.id))

        assert response["id"] == str(job.id)
        assert response["title"] == "Specific Dashboard Job"
        assert response["company_name"] == "Dashboard Detail Co"
        assert response["location"] == "Nairobi"

    def test_empty_job_dataset_returns_empty_response(
        self,
        live_api_client,
    ):
        """Dashboard API receives a valid empty response when no jobs exist."""
        response = live_api_client.get_jobs(
            page=1,
            limit=20,
        )

        assert isinstance(response, dict)
        assert response["data"] == []
        assert response["total"] == 0
        assert response["page"] == 1
        assert response["limit"] == 20

    def test_get_nonexistent_job(self, live_api_client):
        """Dashboard client converts a 404 into APINotFoundError."""
        job_id = str(uuid4())

        with pytest.raises(APINotFoundError):
            live_api_client.get_job(job_id)


class TestDashboardAPIAnalytics:
    """Test dashboard analytics API integration."""

    def test_top_skills(self, live_api_client):
        """Dashboard can retrieve top skills."""
        response = live_api_client.get_top_skills(limit=10)

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)
            assert "skill" in response[0]
            assert "count" in response[0]

    def test_top_companies(self, live_api_client):
        """Dashboard can retrieve top companies."""
        response = live_api_client.get_top_companies(limit=10)

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)

    def test_jobs_by_location(self, live_api_client):
        """Dashboard can retrieve jobs grouped by location."""
        response = live_api_client.get_jobs_by_location(limit=10)

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)

    def test_salary_statistics(self, live_api_client):
        """Dashboard can retrieve aggregate salary statistics."""
        response = live_api_client.get_salary_statistics()

        assert isinstance(response, dict)

    def test_salary_by_location(self, live_api_client):
        """Dashboard can retrieve salary statistics by location."""
        response = live_api_client.get_salary_by_location(limit=10)

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)

    def test_salary_by_company(self, live_api_client):
        """Dashboard can retrieve salary statistics by company."""
        response = live_api_client.get_salary_by_company(limit=10)

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)

    def test_salary_distribution(self, live_api_client):
        """Dashboard can retrieve salary distribution."""
        response = live_api_client.get_salary_distribution()

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)

    def test_employment_types(self, live_api_client):
        """Dashboard can retrieve employment type distribution."""
        response = live_api_client.get_employment_types()

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)

    def test_posting_trend(self, live_api_client):
        """Dashboard can retrieve posting trends."""
        response = live_api_client.get_posting_trend(days=30)

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)

    def test_recent_jobs(self, live_api_client):
        """Dashboard can retrieve the recent jobs count."""
        response = live_api_client.get_recent_jobs(days=7)

        assert isinstance(response, int)
        assert response >= 0

    def test_dataset_summary(self, live_api_client):
        """Dashboard can retrieve the dataset summary."""
        response = live_api_client.get_dataset_summary()

        assert isinstance(response, dict)

    def test_overview(self, live_api_client):
        """Dashboard can retrieve the analytics overview."""
        response = live_api_client.get_overview()

        assert isinstance(response, dict)

    def test_dashboard_summary(self, live_api_client):
        """Dashboard can retrieve the dashboard summary."""
        response = live_api_client.get_dashboard_summary()

        assert isinstance(response, dict)


class TestDashboardAPILanguageAnalytics:
    """Test dashboard language analytics integration."""

    def test_language_distribution(self, live_api_client):
        """Dashboard can retrieve language distribution."""
        response = live_api_client.get_language_distribution()

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)
            assert "language" in response[0]
            assert "count" in response[0]

    def test_language_by_country(self, live_api_client):
        """Dashboard can retrieve language distribution by country."""
        response = live_api_client.get_language_by_country()

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)
            assert "country" in response[0]
            assert "language" in response[0]
            assert "count" in response[0]

    def test_english_vs_non_english(self, live_api_client):
        """Dashboard can retrieve English/non-English distribution."""
        response = live_api_client.get_english_vs_non_english()

        assert isinstance(response, dict)

        if response:
            assert "english_count" in response
            assert "non_english_count" in response
            assert "total_count" in response
            assert "english_percentage" in response

    def test_language_salary_stats(self, live_api_client):
        """Dashboard can retrieve salary statistics by language."""
        response = live_api_client.get_language_salary_stats()

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)
            assert "language" in response[0]


class TestDashboardAPITechnologyAnalytics:
    """Test dashboard technology analytics integration."""

    def test_tech_vs_non_tech(self, live_api_client):
        """Dashboard can retrieve tech/non-tech distribution."""
        response = live_api_client.get_tech_vs_non_tech()

        assert isinstance(response, dict)

        if response:
            assert "tech_count" in response
            assert "non_tech_count" in response
            assert "total_count" in response
            assert "tech_percentage" in response

    def test_tech_category_distribution(self, live_api_client):
        """Dashboard can retrieve technology categories."""
        response = live_api_client.get_tech_category_distribution()

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)
            assert "category" in response[0]
            assert "count" in response[0]

    def test_tech_by_country(self, live_api_client):
        """Dashboard can retrieve technology roles by country."""
        response = live_api_client.get_tech_by_country()

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)
            assert "country" in response[0]
            assert "total_count" in response[0]
            assert "tech_count" in response[0]
            assert "tech_percentage" in response[0]

    def test_tech_skills(self, live_api_client):
        """Dashboard can retrieve skills in technology roles."""
        response = live_api_client.get_tech_skills(limit=20)

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)
            assert "skill" in response[0]
            assert "count" in response[0]

    def test_tech_salary_stats(self, live_api_client):
        """Dashboard can retrieve technology salary statistics."""
        response = live_api_client.get_tech_salary_stats()

        assert isinstance(response, dict)


class TestDashboardAPIEnrichedAnalytics:
    """Test dashboard enriched analytics integration."""

    def test_enriched_skills(self, live_api_client):
        """Dashboard can retrieve enriched skills."""
        response = live_api_client.get_enriched_skills(limit=20)

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)
            assert "skill" in response[0]
            assert "count" in response[0]

    def test_enriched_skills_with_filters(self, live_api_client):
        """Dashboard can retrieve filtered enriched skills."""
        response = live_api_client.get_enriched_skills(
            limit=20,
            country_code="US",
            tech_only=True,
        )

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)
            assert "skill" in response[0]
            assert "count" in response[0]

    def test_enriched_countries(self, live_api_client):
        """Dashboard can retrieve enriched country distribution."""
        response = live_api_client.get_enriched_countries()

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)
            assert "country" in response[0]
            assert "count" in response[0]

    def test_enriched_technology(self, live_api_client):
        """Dashboard can retrieve enriched technology distribution."""
        response = live_api_client.get_enriched_technology()

        assert isinstance(response, list)

        if response:
            assert isinstance(response[0], dict)
            assert "category" in response[0]
            assert "count" in response[0]

    def test_enriched_salary(self, live_api_client):
        """Dashboard can retrieve enriched salary statistics."""
        response = live_api_client.get_enriched_salary()

        assert isinstance(response, dict)

    def test_enriched_salary_with_filters(self, live_api_client):
        """Dashboard can retrieve filtered enriched salary statistics."""
        response = live_api_client.get_enriched_salary(
            country_code="US",
            tech_only=True,
        )

        assert isinstance(response, dict)


class TestDashboardAPIETL:
    """Test dashboard ETL status API integration."""

    def test_last_etl_run(self, live_api_client):
        """Dashboard can retrieve formatted last ETL run information."""
        response = live_api_client.get(
            "api/v1/analytics/etl/last-run"
        )

        assert isinstance(response, dict)
        assert "last_run" in response

    def test_last_etl_run_time(self, live_api_client):
        """Dashboard can retrieve the last ETL run datetime."""
        response = live_api_client.get(
            "api/v1/analytics/etl/last-run-time"
        )

        assert isinstance(response, dict)
        assert "last_run_time" in response

    def test_etl_status(self, live_api_client):
        """Dashboard can retrieve ETL pipeline status."""
        response = live_api_client.get(
            "api/v1/analytics/etl/status"
        )

        assert isinstance(response, dict)
        assert "status" in response

    def test_etl_db_status(self, live_api_client):
        """Dashboard can retrieve database status."""
        response = live_api_client.get(
            "api/v1/analytics/etl/db-status"
        )

        assert isinstance(response, dict)
        assert "status" in response

    def test_companies_count(self, live_api_client):
        """Dashboard can retrieve the number of companies hiring."""
        response = live_api_client.get(
            "api/v1/analytics/companies/count"
        )

        assert isinstance(response, dict)
        assert "count" in response


class TestDashboardAPITransport:
    """Test HTTP transport and exception mapping."""

    def test_timeout_is_converted_to_api_timeout_error(self, api_client):
        """HTTP timeout is converted to APITimeoutError."""
        with patch.object(
            api_client.client,
            "request",
            side_effect=httpx.TimeoutException("timeout"),
        ):
            with pytest.raises(APITimeoutError):
                api_client.get("api/v1/health")

    def test_connection_error_is_converted(self, api_client):
        """Connection failure is converted to APIConnectionError."""
        with patch.object(
            api_client.client,
            "request",
            side_effect=httpx.ConnectError("connection failed"),
        ):
            with pytest.raises(APIConnectionError):
                api_client.get("api/v1/health")

    def test_404_is_converted_to_not_found(self, api_client):
        """HTTP 404 is converted to APINotFoundError."""
        response = httpx.Response(
            404,
            request=httpx.Request(
                "GET",
                "http://testserver/missing",
            ),
            json={"detail": "Not found"},
        )

        with patch.object(
            api_client.client,
            "request",
            return_value=response,
        ):
            with pytest.raises(APINotFoundError):
                api_client.get("api/v1/missing")

    def test_500_is_converted_to_server_error(self, api_client):
        """HTTP 500 is converted to APIServerError."""
        response = httpx.Response(
            500,
            request=httpx.Request(
                "GET",
                "http://testserver/error",
            ),
            json={"detail": "Internal server error"},
        )

        with patch.object(
            api_client.client,
            "request",
            return_value=response,
        ):
            with pytest.raises(APIServerError):
                api_client.get("api/v1/error")
                

def test_dashboard_api_failure_is_not_reported_as_empty_data():
    """API failure must remain distinguishable from a genuinely empty dataset."""
    from dashboard.services.jobs_service import JobsService
    from dashboard.schemas.jobs import JobFilters

    service = JobsService(
        api_client=APIClient(
            base_url="http://127.0.0.1:59999",
            timeout=1,
            retries=0,
        )
    )

    with pytest.raises(Exception):
        service.fetch_jobs(
            filters=JobFilters(is_tech_role=True),
            page=1,
            page_size=20,
        )