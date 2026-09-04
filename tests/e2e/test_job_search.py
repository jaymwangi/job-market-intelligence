"""End-to-end job search workflow tests."""

from datetime import datetime

from app.models.job import Job


def _create_search_jobs(db_session):
    """Create controlled jobs for search validation."""
    jobs = [
        Job(
            title="Python Backend Engineer",
            company_name="Search Tech",
            location="Nairobi",
            description="Python FastAPI backend development",
            salary_min=100000,
            salary_max=150000,
            salary_currency="USD",
            source_site="e2e-search",
            source_id="e2e-search-001",
            source_url="https://example.com/search-001",
            posted_date=datetime.now(),
            scraped_date=datetime.now(),
            is_active=True,
            is_deleted=False,
            language="en",
            country_code="KE",
            employment_type="full-time",
            technology_category="backend",
            is_tech_role=True,
        ),
        Job(
            title="Java Developer",
            company_name="Search Java",
            location="Nairobi",
            description="Java application development",
            salary_min=90000,
            salary_max=140000,
            salary_currency="USD",
            source_site="e2e-search",
            source_id="e2e-search-002",
            source_url="https://example.com/search-002",
            posted_date=datetime.now(),
            scraped_date=datetime.now(),
            is_active=True,
            is_deleted=False,
            language="en",
            country_code="KE",
            employment_type="full-time",
            technology_category="backend",
            is_tech_role=True,
        ),
    ]

    db_session.add_all(jobs)
    db_session.flush()

    return jobs


def test_job_search_end_to_end(api_client, db_session):
    """Search travels from the database through FastAPI to the result."""
    jobs = _create_search_jobs(db_session)

    response = api_client.get(
        "/api/v1/jobs",
        params={
            "q": "Python Backend Engineer",
            "page": 1,
            "limit": 20,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == str(jobs[0].id)
    assert data["data"][0]["title"] == "Python Backend Engineer"