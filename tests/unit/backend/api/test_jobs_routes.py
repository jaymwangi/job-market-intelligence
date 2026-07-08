"""
Unit tests for jobs API routes.
"""

from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.routes.jobs import get_service
from app.main import app


class TestJobsRoutes:
    """Test suite for jobs endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client without database dependency."""
        with TestClient(app) as test_client:
            yield test_client

    @pytest.fixture
    def mock_job(self):
        """Create a mock job."""
        job = Mock()
        job.id = uuid4()
        job.title = "Test Job"
        job.company_name = "Test Company"
        job.location = "San Francisco"
        job.description = "Test description"
        job.salary_min = 100000.0
        job.salary_max = 150000.0
        job.salary_currency = "USD"
        job.posted_date = datetime.now()
        job.source_site = "Test"
        job.source_url = "https://test.com"
        job.is_active = True
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
            data = response.json()
            assert data["total"] >= 1
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
            data = response.json()

            assert "page" in data
            assert "limit" in data
            assert "total" in data
            assert "data" in data
        finally:
            app.dependency_overrides.clear()
