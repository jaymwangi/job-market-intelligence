"""End-to-end dashboard loading workflow tests."""

import pytest

from api.client import APIClient
from dashboard.schemas.jobs import JobFilters
from dashboard.services.jobs_service import JobsService


@pytest.mark.e2e
def test_dashboard_loads_jobs_from_api(
    create_test_jobs,
    api_client,
    monkeypatch,
):
    """Verify PostgreSQL jobs flow through the API into the dashboard."""

    # Arrange: create controlled jobs in the PostgreSQL test database.
    create_test_jobs(
        count=2,
        technology_category="backend",
        is_tech_role=True,
    )

    # The dashboard service normally creates its own HTTP client inside
    # the Streamlit-cached method. Route that call through the existing
    # FastAPI test client so the complete API path is exercised.
    def fetch_jobs(_api_base_url, params):
        response = api_client.get("/api/v1/jobs", params=params)
        response.raise_for_status()
        return response.json()

    monkeypatch.setattr(
        JobsService,
        "_fetch_jobs_cached",
        staticmethod(fetch_jobs),
    )

    dashboard_api_client = APIClient(
        base_url="http://testserver",
        retries=1,
    )

    try:
        # Act: load jobs through the same service used by the dashboard.
        service = JobsService(dashboard_api_client)

        result = service.fetch_jobs(
            filters=JobFilters(),
            page=1,
            page_size=10,
        )

        # Assert: dashboard domain response contains the persisted jobs.
        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 10
        assert result.total_pages == 1

        for job in result.items:
            assert job.title
            assert job.company_name
            assert job.location
            assert job.technology_category == "backend"
            assert job.is_tech_role is True

    finally:
        dashboard_api_client.close()

