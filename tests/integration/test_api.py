"""Integration tests for the FastAPI jobs API.

These tests exercise the real API -> service -> repository -> PostgreSQL
integration-test path.
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app
from app.models.job import Job


class TestJobsAPIIntegration:
    """Integration tests for the jobs API against PostgreSQL."""

    @pytest.fixture
    def client(self, db_session):
        """Create a TestClient using the integration PostgreSQL session."""

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as test_client:
                yield test_client
        finally:
            app.dependency_overrides.clear()

    @staticmethod
    def create_job(
        db_session,
        *,
        title="Integration API Test Job",
        company_name="Integration Test Company",
        location="Nairobi",
        country_code="KE",
        technology_category="backend",
        is_tech_role=True,
        is_active=True,
    ):
        """Create a real Job record in PostgreSQL."""

        job = Job(
            title=title,
            description="Created by API integration test",
            company_name=company_name,
            location=location,
            salary_min=Decimal("50000"),
            salary_max=Decimal("100000"),
            salary_currency="USD",
            source_site=f"integration-{uuid4().hex[:8]}",
            source_id=uuid4().hex,
            source_url="https://example.com/job",
            posted_date=datetime.now(UTC),
            scraped_date=datetime.now(UTC),
            is_active=is_active,
            is_deleted=False,
            technology_category=technology_category,
            is_tech_role=is_tech_role,
            country_code=country_code,
            employment_type="full-time",
            language="en",
        )

        db_session.add(job)
        db_session.flush()

        return job

    def test_get_jobs_returns_postgresql_data(self, client, db_session):
        """GET /jobs returns jobs stored in PostgreSQL."""

        job = self.create_job(db_session)

        response = client.get("/api/v1/jobs")

        assert response.status_code == 200

        data = response.json()

        assert data["total"] >= 1
        assert any(item["id"] == str(job.id) for item in data["data"])

    def test_get_job_by_id_returns_postgresql_record(self, client, db_session):
        """GET /jobs/{id} retrieves a real PostgreSQL record."""

        job = self.create_job(db_session)

        response = client.get(f"/api/v1/jobs/{job.id}")

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == str(job.id)
        assert data["title"] == job.title
        assert data["company_name"] == job.company_name
        assert data["country_code"] == "KE"

    def test_get_job_by_id_returns_404_for_missing_job(
        self,
        client,
    ):
        """GET /jobs/{id} returns 404 for a nonexistent UUID."""

        response = client.get(f"/api/v1/jobs/{uuid4()}")

        assert response.status_code == 404

    def test_get_jobs_pagination_uses_postgresql(
        self,
        client,
        db_session,
    ):
        """Pagination is performed against real PostgreSQL data."""

        jobs = [
            self.create_job(
                db_session,
                title=f"Pagination Job {index}",
            )
            for index in range(3)
        ]

        response = client.get("/api/v1/jobs?page=1&limit=2")

        assert response.status_code == 200

        data = response.json()

        assert data["limit"] == 2
        assert len(data["data"]) == 2
        assert data["total"] >= len(jobs)
        assert data["total_pages"] >= 1

    def test_get_jobs_search_hits_postgresql_data(
        self,
        client,
        db_session,
    ):
        """Search filters real PostgreSQL records."""

        unique_title = f"UniqueIntegrationJob-{uuid4().hex[:8]}"

        job = self.create_job(
            db_session,
            title=unique_title,
        )

        response = client.get(
            "/api/v1/jobs",
            params={"q": unique_title},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] >= 1
        assert any(item["id"] == str(job.id) for item in data["data"])
        
class TestJobsAPIFilterIntegration:
    """Integration tests for job filtering against PostgreSQL."""

    @staticmethod
    def create_job(db_session, **overrides):
        """Create a deterministic PostgreSQL job for filter tests."""

        defaults = {
            "title": "Filter Integration Job",
            "description": "Created for API filter integration testing",
            "company_name": "Filter Test Company",
            "location": "Nairobi",
            "salary_min": Decimal("50000"),
            "salary_max": Decimal("100000"),
            "salary_currency": "USD",
            "source_site": f"filter-{uuid4().hex[:8]}",
            "source_id": uuid4().hex,
            "source_url": "https://example.com/job",
            "posted_date": datetime.now(UTC),
            "scraped_date": datetime.now(UTC),
            "is_active": True,
            "is_deleted": False,
            "country_code": "KE",
            "technology_category": "backend",
            "is_tech_role": True,
            "employment_type": "full-time",
            "language": "en",
        }

        defaults.update(overrides)

        job = Job(**defaults)
        db_session.add(job)
        db_session.flush()

        return job

    @pytest.fixture
    def client(self, db_session):
        """Create a TestClient using the integration PostgreSQL session."""

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as test_client:
                yield test_client
        finally:
            app.dependency_overrides.clear()

    def test_country_filter_uses_postgresql(
        self,
        client,
        db_session,
    ):
        """Country filtering operates on PostgreSQL data."""

        kenya_job = self.create_job(
            db_session,
            title="Kenya Filter Job",
            country_code="KE",
        )
        self.create_job(
            db_session,
            title="US Filter Job",
            country_code="US",
        )

        response = client.get(
            "/api/v1/jobs",
            params={"country_code": "KE"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["data"][0]["id"] == str(kenya_job.id)

    def test_technology_category_filter_uses_postgresql(
        self,
        client,
        db_session,
    ):
        """Technology category filtering operates on PostgreSQL data."""

        backend_job = self.create_job(
            db_session,
            title="Backend Filter Job",
            technology_category="backend",
        )
        self.create_job(
            db_session,
            title="Frontend Filter Job",
            technology_category="frontend",
        )

        response = client.get(
            "/api/v1/jobs",
            params={"technology_category": "backend"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["data"][0]["id"] == str(backend_job.id)

    def test_is_tech_role_filter_uses_postgresql(
        self,
        client,
        db_session,
    ):
        """Tech-role filtering operates on PostgreSQL data."""

        tech_job = self.create_job(
            db_session,
            title="Tech Filter Job",
            is_tech_role=True,
        )
        self.create_job(
            db_session,
            title="Non Tech Filter Job",
            is_tech_role=False,
            technology_category=None,
        )

        response = client.get(
            "/api/v1/jobs",
            params={"is_tech_role": True},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["data"][0]["id"] == str(tech_job.id)

    def test_salary_range_filters_use_postgresql(
        self,
        client,
        db_session,
    ):
        """Salary filters operate on PostgreSQL data."""

        matching_job = self.create_job(
            db_session,
            title="Salary Match Job",
            salary_min=Decimal("80000"),
            salary_max=Decimal("120000"),
        )
        self.create_job(
            db_session,
            title="Salary Outside Job",
            salary_min=Decimal("20000"),
            salary_max=Decimal("40000"),
        )

        response = client.get(
            "/api/v1/jobs",
            params={
                "min_salary": 70000,
                "max_salary": 130000,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["data"][0]["id"] == str(matching_job.id)

    def test_combined_filters_use_postgresql(
        self,
        client,
        db_session,
    ):
        """Multiple filters are applied together against PostgreSQL."""

        matching_job = self.create_job(
            db_session,
            title="Combined Filter Match",
            country_code="KE",
            technology_category="backend",
            is_tech_role=True,
            employment_type="full-time",
        )

        self.create_job(
            db_session,
            title="Wrong Country",
            country_code="US",
            technology_category="backend",
            is_tech_role=True,
            employment_type="full-time",
        )

        self.create_job(
            db_session,
            title="Wrong Category",
            country_code="KE",
            technology_category="frontend",
            is_tech_role=True,
            employment_type="full-time",
        )

        response = client.get(
            "/api/v1/jobs",
            params={
                "country_code": "KE",
                "technology_category": "backend",
                "is_tech_role": True,
                "employment_type": "full-time",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["data"][0]["id"] == str(matching_job.id)

    def test_filter_with_no_matches_returns_empty_data(
        self,
        client,
        db_session,
    ):
        """A filter with no matching PostgreSQL records returns empty data."""

        self.create_job(
            db_session,
            country_code="KE",
        )

        response = client.get(
            "/api/v1/jobs",
            params={"country_code": "ZZ"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 0
        assert data["data"] == []
        assert data["total_pages"] == 0