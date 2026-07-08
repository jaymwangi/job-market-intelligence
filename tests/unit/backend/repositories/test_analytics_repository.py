"""
Unit tests for analytics repository.
"""

from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.repositories.analytics_repository import AnalyticsRepository


class TestAnalyticsRepository:
    """Test suite for analytics repository operations."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance with mock db."""
        return AnalyticsRepository(mock_db)

    def test_init(self, repository, mock_db):
        """Test repository initialization."""
        assert repository.db == mock_db

    def test_apply_source_filter_with_source(self, repository):
        """Test applying source filter with source_site."""
        mock_query = Mock()
        result = repository._apply_source_filter(mock_query, "adzuna")
        mock_query.filter.assert_called_once()
        assert result == mock_query.filter.return_value

    def test_apply_source_filter_without_source(self, repository):
        """Test applying source filter without source_site."""
        mock_query = Mock()
        result = repository._apply_source_filter(mock_query, None)
        assert result == mock_query
        mock_query.filter.assert_not_called()

    def test_apply_active_filter(self, repository):
        """Test applying active filter."""
        mock_query = Mock()
        result = repository._apply_active_filter(mock_query)
        mock_query.filter.assert_called()
        assert result == mock_query.filter.return_value

    def test_get_top_skills_empty(self, repository):
        """Test getting top skills with no data."""
        repository.db.query.return_value.join.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = repository.get_top_skills(limit=5)
        assert result == []

    def test_get_top_skills_with_data(self, repository):
        """Test getting top skills with data."""
        mock_results = [Mock(skill="Python", count=450), Mock(skill="JavaScript", count=380)]
        repository.db.query.return_value.join.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
            mock_results
        )

        result = repository.get_top_skills(limit=2)
        assert len(result) == 2
        assert result[0]["skill"] == "Python"
        assert result[0]["count"] == 450

    def test_get_top_companies_empty(self, repository):
        """Test getting top companies with no data."""
        repository.db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = repository.get_top_companies(limit=5)
        assert result == []

    def test_get_top_companies_with_data(self, repository):
        """Test getting top companies with data."""
        mock_results = [
            Mock(company="TechCorp", job_count=120),
            Mock(company="DataInc", job_count=80),
        ]
        repository.db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
            mock_results
        )

        result = repository.get_top_companies(limit=2)
        assert len(result) == 2
        assert result[0]["company"] == "TechCorp"
        assert result[0]["job_count"] == 120

    def test_get_jobs_by_location_empty(self, repository):
        """Test getting jobs by location with no data."""
        repository.db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = repository.get_jobs_by_location(limit=5)
        assert result == []

    def test_get_jobs_by_location_with_data(self, repository):
        """Test getting jobs by location with data."""
        mock_results = [
            Mock(location="San Francisco", job_count=200),
            Mock(location="New York", job_count=150),
        ]
        repository.db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
            mock_results
        )

        result = repository.get_jobs_by_location(limit=2)
        assert len(result) == 2
        assert result[0]["location"] == "San Francisco"
        assert result[0]["job_count"] == 200

    def test_get_salary_statistics_no_data(self, repository):
        """Test getting salary statistics with no data."""
        # Mock the stats query to return None
        repository.db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.first.return_value = (
            None
        )
        # Mock the median query to return empty
        repository.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )

        result = repository.get_salary_statistics()
        assert result["sample_size"] == 0
        assert result["average"] is None

    def test_get_total_jobs(self, repository):
        """Test getting total jobs count."""
        repository.db.query.return_value.filter.return_value.count.return_value = 1000

        result = repository.get_total_jobs()
        assert result == 1000

    def test_count_recent_jobs(self, repository):
        """Test counting recent jobs."""
        repository.db.query.return_value.filter.return_value.scalar.return_value = 50

        result = repository.count_recent_jobs(days=7)
        assert result == 50
