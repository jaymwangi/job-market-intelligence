"""
Unit tests for job service.
"""

from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.job import Job
from app.schemas.job import JobFilters
from app.services.job_service import JobService


class TestJobService:
    """Test suite for JobService."""

    @pytest.fixture
    def mock_repo(self):
        """Create a mock repository."""
        repo = Mock()
        repo.get_jobs.return_value = []
        repo.count_jobs.return_value = 0
        repo.get_by_id.return_value = None
        return repo

    @pytest.fixture
    def service(self, mock_repo):
        return JobService(mock_repo)

    def test_get_jobs_success(self, service, mock_repo):
        """Test getting jobs successfully."""
        # Setup mock
        mock_repo.get_jobs.return_value = [Job(title="Job 1"), Job(title="Job 2")]
        mock_repo.count_jobs.return_value = 2

        jobs, total = service.get_jobs(page=1, limit=10, filters=JobFilters(), search_query=None)

        assert len(jobs) == 2
        assert total == 2
        mock_repo.get_jobs.assert_called_once()
        mock_repo.count_jobs.assert_called_once()

    def test_get_jobs_with_filters(self, service, mock_repo):
        """Test getting jobs with filters."""
        filters = JobFilters(company_name="TechCorp", location="SF", min_salary=100000)

        service.get_jobs(page=1, limit=10, filters=filters)

        mock_repo.get_jobs.assert_called_with(filters, 0, 10, None)

    def test_get_jobs_with_search(self, service, mock_repo):
        """Test getting jobs with search query."""
        service.get_jobs(page=1, limit=10, filters=JobFilters(), search_query="Python")

        mock_repo.get_jobs.assert_called_with(JobFilters(), 0, 10, "Python")

    def test_get_jobs_invalid_page(self, service):
        """Test getting jobs with invalid page."""
        with pytest.raises(HTTPException) as exc_info:
            service.get_jobs(page=0, limit=10, filters=JobFilters())

        assert exc_info.value.status_code == 400
        assert "page must be >= 1" in str(exc_info.value.detail)

    def test_get_jobs_invalid_limit_too_low(self, service):
        """Test getting jobs with limit too low."""
        with pytest.raises(HTTPException) as exc_info:
            service.get_jobs(page=1, limit=0, filters=JobFilters())

        assert exc_info.value.status_code == 400
        assert "limit must be between 1 and 100" in str(exc_info.value.detail)

    def test_get_jobs_invalid_limit_too_high(self, service):
        """Test getting jobs with limit too high."""
        with pytest.raises(HTTPException) as exc_info:
            service.get_jobs(page=1, limit=101, filters=JobFilters())

        assert exc_info.value.status_code == 400
        assert "limit must be between 1 and 100" in str(exc_info.value.detail)

    def test_get_jobs_repository_error(self, service, mock_repo):
        """Test getting jobs when repository raises error."""
        mock_repo.get_jobs.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            service.get_jobs(page=1, limit=10, filters=JobFilters())

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve jobs" in str(exc_info.value.detail)

    def test_get_job_by_id_success(self, service, mock_repo):
        """Test getting job by ID successfully."""
        job_id = uuid4()
        expected_job = Job(id=job_id, title="Test Job")
        mock_repo.get_by_id.return_value = expected_job

        job = service.get_job(job_id)

        assert job == expected_job
        mock_repo.get_by_id.assert_called_with(job_id)

    def test_get_job_by_id_not_found(self, service, mock_repo):
        """Test getting job by ID when not found."""
        job_id = uuid4()
        mock_repo.get_by_id.return_value = None

        job = service.get_job(job_id)

        assert job is None
        mock_repo.get_by_id.assert_called_with(job_id)

    def test_get_job_by_id_repository_error(self, service, mock_repo):
        """Test getting job by ID when repository raises error."""
        job_id = uuid4()
        mock_repo.get_by_id.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            service.get_job(job_id)

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve job" in str(exc_info.value.detail)

    def test_get_jobs_pagination_calculation(self, service, mock_repo):
        """Test pagination offset calculation."""
        # Page 2 with limit 20 should have offset 20
        service.get_jobs(page=2, limit=20, filters=JobFilters())
        mock_repo.get_jobs.assert_called_with(JobFilters(), 20, 20, None)

        # Page 3 with limit 10 should have offset 20
        service.get_jobs(page=3, limit=10, filters=JobFilters())
        mock_repo.get_jobs.assert_called_with(JobFilters(), 20, 10, None)
