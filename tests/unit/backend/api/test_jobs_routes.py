"""
Unit tests for jobs API routes.
"""

from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock

from app.api.routes.jobs import get_service
from app.main import app
from app.services.job_service import JobService


class TestJobsRoutes:
    """Test suite for jobs endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client without database dependency."""
        with TestClient(app) as test_client:
            yield test_client

    @pytest.fixture
    def mock_job(self):
        """Create a mock job matching the JobResponse contract."""
        job = Mock()

        # Core job fields
        job.id = uuid4()
        job.title = "Test Job"
        job.company_name = "Test Company"
        job.location = "San Francisco"
        job.description = "Test description"

        # Salary fields
        job.salary_min = 100000.0
        job.salary_max = 150000.0
        job.salary_currency = "USD"

        # Source fields
        job.source_site = "Test"
        job.source_url = "https://test.com"

        # Job metadata
        job.posted_date = datetime.now()
        job.is_active = True

        # Enrichment fields required by JobResponse.from_model()
        job.language = "en"
        job.skills = []
        job.technology_category = "backend"
        job.is_tech_role = True
        job.country_code = "US"
        job.employment_type = "FULL_TIME"

        return job

    def test_get_jobs_empty(self, client):
        """Test getting jobs when none exist."""
        mock_service = Mock()
        mock_service.get_jobs.return_value = ([], 0)

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs")

            assert response.status_code == 200

            data = response.json()

            assert data["total"] == 0
            assert len(data["data"]) == 0
            assert data["page"] == 1
            assert data["limit"] == 20
        finally:
            app.dependency_overrides.clear()

    def test_get_jobs_with_data(self, client, mock_job):
        """Test getting jobs with existing data."""
        mock_service = Mock()
        mock_service.get_jobs.return_value = ([mock_job], 1)

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs")

            assert response.status_code == 200

            data = response.json()

            assert data["total"] == 1
            assert len(data["data"]) == 1
        finally:
            app.dependency_overrides.clear()

    def test_get_jobs_pagination(self, client, mock_job):
        """Test job listing with pagination."""
        mock_service = Mock()
        mock_service.get_jobs.return_value = ([mock_job] * 5, 10)

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs?page=1&limit=5")

            assert response.status_code == 200

            data = response.json()

            assert len(data["data"]) == 5
            assert data["total"] == 10
            assert data["page"] == 1
            assert data["limit"] == 5
        finally:
            app.dependency_overrides.clear()

    def test_get_jobs_with_search(self, client, mock_job):
        """Test job listing with search query."""
        mock_service = Mock()
        mock_service.get_jobs.return_value = ([mock_job], 1)

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs?q=Test")

            assert response.status_code == 200

            data = response.json()

            assert data["total"] == 1
            assert len(data["data"]) == 1
        finally:
            app.dependency_overrides.clear()

    def test_get_jobs_with_filters(self, client, mock_job):
        """Test job listing with filters."""
        mock_service = Mock()
        mock_service.get_jobs.return_value = ([mock_job], 1)

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs?location=San Francisco")

            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_get_jobs_invalid_salary_range(self, client):
        """Test job listing with invalid salary range."""
        mock_service = Mock()

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs?min_salary=200000&max_salary=100000")

            assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()

    def test_get_jobs_invalid_page(self, client):
        """Test job listing with invalid page number."""
        mock_service = Mock()

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs?page=0")

            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_get_jobs_invalid_limit(self, client):
        """Test job listing with invalid limit."""
        mock_service = Mock()

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs?limit=200")

            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_get_job_by_id_success(self, client, mock_job):
        """Test getting a specific job by ID."""
        mock_service = Mock()
        mock_service.get_job.return_value = mock_job

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            job_id = mock_job.id

            response = client.get(f"/api/v1/jobs/{job_id}")

            assert response.status_code == 200

            data = response.json()

            assert data["id"] == str(job_id)
        finally:
            app.dependency_overrides.clear()

    def test_get_job_by_id_not_found(self, client):
        """Test getting non-existent job."""
        mock_service = Mock()
        mock_service.get_job.return_value = None

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            fake_id = uuid4()

            response = client.get(f"/api/v1/jobs/{fake_id}")

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_get_job_by_id_invalid_uuid(self, client):
        """Test getting job with invalid UUID format."""
        mock_service = Mock()

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs/invalid-uuid")

            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_jobs_response_structure(self, client, mock_job):
        """Test job list response structure."""
        mock_service = Mock()
        mock_service.get_jobs.return_value = ([mock_job], 1)

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs")

            assert response.status_code == 200

            data = response.json()

            assert "page" in data
            assert "limit" in data
            assert "total" in data
            assert "data" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_service_creates_job_service(self):
        """Test the service dependency creates a JobService."""
        db = Mock()

        service = get_service(db)

        assert service is not None
        assert isinstance(service, JobService)

    def test_get_top_skills(self, client):
        """Test getting top skills."""
        mock_service = Mock()
        mock_service.get_top_skills.return_value = [
            {"skill": "Python", "count": 10},
            {"skill": "SQL", "count": 8},
        ]

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs/skills/top")

            assert response.status_code == 200
            assert response.json() == [
                {"skill": "Python", "count": 10},
                {"skill": "SQL", "count": 8},
            ]
            mock_service.get_top_skills.assert_called_once_with(20, None)
        finally:
            app.dependency_overrides.clear()

    def test_get_top_skills_with_filters(self, client):
        """Test getting top skills with limit and country filter."""
        mock_service = Mock()
        mock_service.get_top_skills.return_value = [
            {"skill": "Python", "count": 5},
        ]

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs/skills/top?limit=10&country_code=KE")

            assert response.status_code == 200
            assert response.json() == [{"skill": "Python", "count": 5}]
            mock_service.get_top_skills.assert_called_once_with(10, "KE")
        finally:
            app.dependency_overrides.clear()

    def test_get_country_distribution(self, client):
        """Test getting job distribution by country."""
        mock_service = Mock()
        mock_service.get_country_distribution.return_value = [
            {"country_code": "US", "count": 20},
            {"country_code": "KE", "count": 10},
        ]

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs/countries/distribution")

            assert response.status_code == 200
            assert response.json() == [
                {"country_code": "US", "count": 20},
                {"country_code": "KE", "count": 10},
            ]
            mock_service.get_country_distribution.assert_called_once_with()
        finally:
            app.dependency_overrides.clear()

    def test_get_technology_distribution(self, client):
        """Test getting technology distribution."""
        mock_service = Mock()
        mock_service.get_technology_distribution.return_value = [
            {"category": "backend", "count": 15},
            {"category": "frontend", "count": 8},
        ]

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs/technology/distribution")

            assert response.status_code == 200
            assert response.json() == [
                {"category": "backend", "count": 15},
                {"category": "frontend", "count": 8},
            ]
            mock_service.get_technology_distribution.assert_called_once_with()
        finally:
            app.dependency_overrides.clear()

    def test_get_job_stats(self, client):
        """Test getting job statistics."""
        mock_service = Mock()
        mock_service.get_stats.return_value = {
            "total_jobs": 100,
            "total_companies": 50,
            "total_countries": 10,
            "total_skills": 75,
            "average_salary_min": 50000.0,
            "average_salary_max": 90000.0,
            "tech_role_count": 60,
        }

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/jobs/stats/summary")

            assert response.status_code == 200
            assert response.json() == mock_service.get_stats.return_value
            mock_service.get_stats.assert_called_once_with()
        finally:
            app.dependency_overrides.clear()

    def test_translate_job_not_found(self, client):
        """Test translation when the job does not exist."""
        mock_service = Mock()
        mock_service.get_job.return_value = None

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.post(f"/api/v1/jobs/{uuid4()}/translate")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    def test_translate_job_already_in_target_language(self, client, mock_job):
        """Test translation when job is already in the target language."""
        mock_job.language = "en"

        mock_service = Mock()
        mock_service.get_job.return_value = mock_job

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.post(
                f"/api/v1/jobs/{mock_job.id}/translate?target_language=en"
            )

            assert response.status_code == 200

            data = response.json()
            assert data["job_id"] == str(mock_job.id)
            assert data["source_language"] == "en"
            assert data["target_language"] == "en"
            assert data["needs_translation"] is False
            assert data["translated_title"] == mock_job.title
            assert data["translated_description"] == mock_job.description
        finally:
            app.dependency_overrides.clear()

    def test_translate_job_success(self, client, mock_job, monkeypatch):
        """Test successful job translation."""
        mock_job.language = "fr"

        mock_service = Mock()
        mock_service.get_job.return_value = mock_job

        translation_service = Mock()
        translation_service.translate = AsyncMock(
            return_value=Mock(
                text="Translated job description",
                success=True,
                duration_ms=125.5,
                character_count=28,
                error=None,
            )
        )

        async_get_translation_service = AsyncMock(
            return_value=translation_service
        )

        monkeypatch.setattr(
            "app.api.routes.jobs.get_translation_service",
            async_get_translation_service,
        )

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.post(
                f"/api/v1/jobs/{mock_job.id}/translate?target_language=en"
            )

            assert response.status_code == 200

            data = response.json()
            assert data["job_id"] == str(mock_job.id)
            assert data["source_language"] == "fr"
            assert data["target_language"] == "en"
            assert data["needs_translation"] is True
            assert data["translated_title"] == "Translated job description"
            assert data["translated_description"] == "Translated job description"
            assert data["success"] is True
            assert data["duration_ms"] == 125.5
            assert data["character_count"] == 28
            assert data["error"] is None

            translation_service.translate.assert_awaited_once_with(
                text=mock_job.description,
                source_language="fr",
                target_language="en",
            )
        finally:
            app.dependency_overrides.clear()

    def test_translate_job_failed_translation(self, client, mock_job, monkeypatch):
        """Test translation service returning an unsuccessful result."""
        mock_job.language = "fr"

        mock_service = Mock()
        mock_service.get_job.return_value = mock_job

        translation_service = Mock()
        translation_service.translate = AsyncMock(
            return_value=Mock(
                text=None,
                success=False,
                duration_ms=50.0,
                character_count=0,
                error=ValueError("Translation unavailable"),
            )
        )

        monkeypatch.setattr(
            "app.api.routes.jobs.get_translation_service",
            AsyncMock(return_value=translation_service),
        )

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.post(
                f"/api/v1/jobs/{mock_job.id}/translate?target_language=en"
            )

            assert response.status_code == 200

            data = response.json()
            assert data["needs_translation"] is True
            assert data["translated_title"] == mock_job.title
            assert data["translated_description"] == mock_job.description
            assert data["success"] is False
            assert data["duration_ms"] == 50.0
            assert data["character_count"] == 0
            assert data["error"] == "Translation unavailable"
        finally:
            app.dependency_overrides.clear()

    def test_translate_job_exception(self, client, mock_job, monkeypatch):
        """Test translation endpoint when the translation service raises."""
        mock_job.language = "fr"

        mock_service = Mock()
        mock_service.get_job.return_value = mock_job

        translation_service = Mock()
        translation_service.translate = AsyncMock(
            side_effect=RuntimeError("Translation service failed")
        )

        monkeypatch.setattr(
            "app.api.routes.jobs.get_translation_service",
            AsyncMock(return_value=translation_service),
        )

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.post(
                f"/api/v1/jobs/{mock_job.id}/translate?target_language=en"
            )

            assert response.status_code == 500
            assert response.json()["detail"] == (
                "Translation failed: Translation service failed"
            )
        finally:
            app.dependency_overrides.clear()