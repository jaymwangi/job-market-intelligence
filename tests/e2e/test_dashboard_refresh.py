"""End-to-end ETL → API → dashboard refresh workflow tests."""

import pytest

from api.client import APIClient
from app.etl import ETLPipeline
from dashboard.schemas.jobs import JobFilters
from dashboard.services.jobs_service import JobsService


@pytest.mark.e2e
def test_etl_to_api_to_dashboard_refresh(
    db_session,
    api_client,
    monkeypatch,
):
    """Verify ETL data becomes visible through the API and dashboard."""

    raw_jobs = [
        {
            "id": "e2e-dashboard-001",
            "title": "Python Backend Engineer",
            "description": (
                "Build backend services using Python FastAPI PostgreSQL "
                "and Docker."
            ),
            "company": {
                "display_name": "E2E Technology Ltd",
            },
            "location": {
                "display_name": "Nairobi, Kenya",
            },
            "redirect_url": "https://example.com/jobs/e2e-dashboard-001",
            "created": "2026-09-04T08:00:00Z",
            "salary_min": 120000,
            "salary_max": 180000,
            "salary_is_predicted": False,
            "contract_type": "permanent",
            "contract_time": "full_time",
            "category": {
                "label": "IT Jobs",
                "tag": "it-jobs",
            },
        }
    ]

    # Arrange: run the real ETL pipeline against the PostgreSQL
    # integration-test transaction.
    pipeline = ETLPipeline(db_session=db_session)

    monkeypatch.setattr(
        pipeline.extractor,
        "extract",
        lambda *args, **kwargs: raw_jobs,
    )

    metrics = pipeline.run(
        countries=["ke"],
        use_acquisition=False,
    )

    # Verify the ETL stage completed successfully.
    assert metrics.extracted == 1
    assert metrics.transformed == 1
    assert metrics.enriched == 1
    assert metrics.validated == 1
    assert metrics.inserted == 1

    # Verify the API can retrieve the ETL-created job.
    response = api_client.get(
        "/api/v1/jobs",
        params={"q": "Python Backend Engineer"},
    )

    assert response.status_code == 200

    api_data = response.json()
    print("\nAPI RESPONSE:", api_data)

    assert api_data["total"] == 1
    assert len(api_data["data"]) == 1

    api_job = api_data["data"][0]

    assert api_job["title"] == "Python Backend Engineer"
    assert api_job["company_name"] == "E2E Technology Ltd"
    assert api_job["country_code"] == "KE"
    assert api_job["is_tech_role"] is True

    # Route the dashboard service through the same live FastAPI test
    # application. This preserves the complete ETL → PostgreSQL → API
    # → dashboard data path without making a real network request.
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
        # Act: refresh/load the job through the dashboard service.
        service = JobsService(dashboard_api_client)

        dashboard_result = service.fetch_jobs(
            filters=JobFilters(
                search="Python Backend Engineer",
            ),
            page=1,
            page_size=10,
        )

        # Assert: the dashboard receives the same ETL-created job.
        assert dashboard_result.total == 1
        assert len(dashboard_result.items) == 1

        dashboard_job = dashboard_result.items[0]

        assert dashboard_job.title == "Python Backend Engineer"
        assert dashboard_job.company_name == "E2E Technology Ltd"
        assert dashboard_job.country_code == "KE"
        assert dashboard_job.is_tech_role is True

    finally:
        dashboard_api_client.close()

