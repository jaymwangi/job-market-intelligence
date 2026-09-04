"""End-to-end job filtering workflow tests."""

from datetime import datetime

from app.models.job import Job


def _create_filter_jobs(db_session):
    """Create controlled jobs for filter validation."""
    jobs = [
        Job(
            title="Backend Engineer",
            company_name="Filter Tech",
            location="London",
            description="Python backend engineering",
            salary_min=100000,
            salary_max=150000,
            salary_currency="GBP",
            source_site="e2e-filter",
            source_id="e2e-filter-001",
            source_url="https://example.com/filter-001",
            posted_date=datetime.now(),
            scraped_date=datetime.now(),
            is_active=True,
            is_deleted=False,
            language="en",
            country_code="GB",
            employment_type="full-time",
            technology_category="backend",
            is_tech_role=True,
        ),
        Job(
            title="Frontend Engineer",
            company_name="Filter Frontend",
            location="London",
            description="Frontend development",
            salary_min=90000,
            salary_max=130000,
            salary_currency="GBP",
            source_site="e2e-filter",
            source_id="e2e-filter-002",
            source_url="https://example.com/filter-002",
            posted_date=datetime.now(),
            scraped_date=datetime.now(),
            is_active=True,
            is_deleted=False,
            language="en",
            country_code="GB",
            employment_type="full-time",
            technology_category="frontend",
            is_tech_role=True,
        ),
        Job(
            title="Backend Engineer",
            company_name="Filter Nairobi",
            location="Nairobi",
            description="Python backend engineering",
            salary_min=80000,
            salary_max=120000,
            salary_currency="USD",
            source_site="e2e-filter",
            source_id="e2e-filter-003",
            source_url="https://example.com/filter-003",
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


def test_job_filters_end_to_end(api_client, db_session):
    """Database data is filtered correctly through the API."""
    jobs = _create_filter_jobs(db_session)

    response = api_client.get(
        "/api/v1/jobs",
        params={
            "location": "London",
            "technology_category": "backend",
            "is_tech_role": "true",
            "page": 1,
            "limit": 20,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["data"]) == 1

    result = data["data"][0]

    assert result["id"] == str(jobs[0].id)
    assert result["location"] == "London"
    assert result["technology_category"] == "backend"
    assert result["is_tech_role"] is True


def test_job_salary_filter_end_to_end(api_client, db_session):
    """Salary filtering is applied to PostgreSQL-backed API results."""
    _create_filter_jobs(db_session)

    response = api_client.get(
        "/api/v1/jobs",
        params={
            "min_salary": 95000,
            "max_salary": 155000,
            "page": 1,
            "limit": 20,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1

    for job in data["data"]:
        assert job["salary_max"] >= 95000
        assert job["salary_min"] <= 155000