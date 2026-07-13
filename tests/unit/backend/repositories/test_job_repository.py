"""
Unit tests for job repository.
"""

from datetime import UTC, datetime
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.repositories.job_repository import JobRepository
from app.schemas.job import JobFilters


class TestJobRepository:
    """Test suite for job repository operations."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance with mock db."""
        return JobRepository(mock_db)

    @pytest.fixture
    def mock_job_validated(self):
        """Create a mock validated job."""
        mock = Mock()
        mock.title = "Python Developer"
        mock.description = "Test description"
        mock.company_name = "TechCorp"
        mock.location = "San Francisco"
        mock.salary_min = 100000.0
        mock.salary_max = 150000.0
        mock.currency = "USD"
        mock.source = "adzuna"
        mock.external_id = "job_123"
        mock.source_url = "https://example.com/job/123"
        mock.posted_date = datetime.now(UTC)
        return mock

    def test_init(self, repository, mock_db):
        """Test repository initialization."""
        assert repository.session == mock_db

    def test_exists_true(self, repository, mock_db):
        """Test exists returns True when job found."""
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()

        result = repository.exists("adzuna", "job_123")
        assert result is True

    def test_exists_false(self, repository, mock_db):
        """Test exists returns False when job not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = repository.exists("adzuna", "nonexistent")
        assert result is False

    def test_get_by_source_found(self, repository, mock_db):
        """Test get_by_source returns job when found."""
        mock_job = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        result = repository.get_by_source("adzuna", "job_123")
        assert result == mock_job

    def test_get_by_source_not_found(self, repository, mock_db):
        """Test get_by_source returns None when not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = repository.get_by_source("adzuna", "nonexistent")
        assert result is None

    def test_create_from_validated(self, repository, mock_db, mock_job_validated):
        """Test creating a job from validated model."""
        mock_job = Mock()
        mock_db.add.return_value = None
        mock_db.flush.return_value = None

        # Patch Job to return our mock
        with patch("app.repositories.job_repository.Job") as MockJob:
            MockJob.return_value = mock_job

            result = repository.create_from_validated(mock_job_validated)

            assert result == mock_job
            MockJob.assert_called_once()
            mock_db.add.assert_called_once_with(mock_job)
            mock_db.flush.assert_called_once()

    def test_apply_filters_no_filters(self, repository):
        """Test apply_filters with no filters."""
        mock_query = Mock()
        filters = JobFilters()

        result = repository._apply_filters(mock_query, filters, None)
        mock_query.filter.assert_called()
        assert result == mock_query.filter.return_value

    def test_apply_filters_with_company(self, repository):
        """Test apply_filters with company filter."""
        mock_query = Mock()
        filters = JobFilters(company_name="TechCorp")

        result = repository._apply_filters(mock_query, filters, None)
        mock_query.filter.assert_called()
        assert result == mock_query.filter.return_value

    def test_apply_filters_with_location(self, repository):
        """Test apply_filters with location filter."""
        mock_query = Mock()
        filters = JobFilters(location="San Francisco")

        result = repository._apply_filters(mock_query, filters, None)
        mock_query.filter.assert_called()
        assert result == mock_query.filter.return_value

    def test_apply_filters_with_search(self, repository):
        """Test apply_filters with search query."""
        mock_query = Mock()
        filters = JobFilters()

        result = repository._apply_filters(mock_query, filters, "Python")
        mock_query.filter.assert_called()
        assert result == mock_query.filter.return_value

    def test_apply_filters_with_salary_range(self, repository):
        """Test apply_filters with salary range."""
        mock_query = Mock()
        filters = JobFilters(min_salary=100000.0, max_salary=150000.0)

        result = repository._apply_filters(mock_query, filters, None)
        mock_query.filter.assert_called()
        assert result == mock_query.filter.return_value

    def test_get_jobs_empty(self, repository, mock_db):
        """Test get_jobs returns empty list."""
        mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )

        filters = JobFilters()
        result = repository.get_jobs(filters, 0, 20, None)
        assert result == []

    def test_get_jobs_with_data(self, repository, mock_db):
        """Test get_jobs returns data."""
        mock_jobs = [Mock(), Mock()]
        mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            mock_jobs
        )

        filters = JobFilters()
        result = repository.get_jobs(filters, 0, 20, None)
        assert len(result) == 2

    def test_count_jobs(self, repository, mock_db):
        """Test count_jobs returns count."""
        mock_db.query.return_value.count.return_value = 10

        filters = JobFilters()
        result = repository.count_jobs(filters, None)
        assert result == 10

    def test_get_by_id_found(self, repository, mock_db):
        """Test get_by_id returns job when found."""
        mock_job = Mock()
        job_id = uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        result = repository.get_by_id(job_id)
        assert result == mock_job

    def test_get_by_id_not_found(self, repository, mock_db):
        """Test get_by_id returns None when not found."""
        job_id = uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = repository.get_by_id(job_id)
        assert result is None
