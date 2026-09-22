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

    @pytest.fixture
    def mock_query(self, mock_db):
        """Create a reusable mock SQLAlchemy query chain."""
        query = Mock()

        query.filter.return_value = query
        query.join.return_value = query
        query.group_by.return_value = query
        query.order_by.return_value = query
        query.limit.return_value = query
        query.offset.return_value = query

        mock_db.query.return_value = query

        return query

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

    def test_apply_language_filter_with_language(self, repository, mock_query):
        """Test applying a language filter."""
        result = repository._apply_language_filter(mock_query, "Python")

        assert result is mock_query
        mock_query.filter.assert_called_once()

    def test_apply_language_filter_without_language(self, repository, mock_query):
        """Test skipping language filter when no language is provided."""
        result = repository._apply_language_filter(mock_query)

        assert result is mock_query
        mock_query.filter.assert_not_called()

    def test_apply_active_filter(self, repository):
        """Test applying active filter."""
        mock_query = Mock()

        result = repository._apply_active_filter(mock_query)

        mock_query.filter.assert_called_once()
        assert result == mock_query.filter.return_value

    def test_get_top_skills_empty(self, repository, mock_query):
        """Test getting top skills with no data."""
        mock_query.all.return_value = []

        result = repository.get_top_skills(limit=5)

        assert result == []

    def test_get_top_skills_with_data(self, repository, mock_query):
        """Test getting top skills with data."""
        mock_query.all.return_value = [
            Mock(skill="Python", count=450),
            Mock(skill="JavaScript", count=380),
        ]

        result = repository.get_top_skills(limit=2)

        assert len(result) == 2
        assert result[0]["skill"] == "Python"
        assert result[0]["count"] == 450
        assert result[1]["skill"] == "JavaScript"
        assert result[1]["count"] == 380

    def test_get_top_companies_empty(self, repository, mock_query):
        """Test getting top companies with no data."""
        mock_query.all.return_value = []

        result = repository.get_top_companies(limit=5)

        assert result == []

    def test_get_top_companies_with_data(self, repository, mock_query):
        """Test getting top companies with data."""
        mock_query.all.return_value = [
            Mock(company="TechCorp", job_count=120),
            Mock(company="DataInc", job_count=80),
        ]

        result = repository.get_top_companies(limit=2)

        assert len(result) == 2
        assert result[0]["company"] == "TechCorp"
        assert result[0]["job_count"] == 120
        assert result[1]["company"] == "DataInc"
        assert result[1]["job_count"] == 80

    def test_get_jobs_by_location_empty(self, repository, mock_query):
        """Test getting jobs by location with no data."""
        mock_query.all.return_value = []

        result = repository.get_jobs_by_location(limit=5)

        assert result == []

    def test_get_jobs_by_location_with_data(self, repository, mock_query):
        """Test getting jobs by location with data."""
        mock_query.all.return_value = [
            Mock(location="San Francisco", job_count=200),
            Mock(location="New York", job_count=150),
        ]

        result = repository.get_jobs_by_location(limit=2)

        assert len(result) == 2
        assert result[0]["location"] == "San Francisco"
        assert result[0]["job_count"] == 200
        assert result[1]["location"] == "New York"
        assert result[1]["job_count"] == 150

    def test_get_salary_statistics_no_data(self, repository, mock_db):
        """Test getting salary statistics with no data."""
        stats_query = Mock()
        stats_query.filter.return_value = stats_query
        stats_query.group_by.return_value = stats_query
        stats_query.order_by.return_value = stats_query
        stats_query.first.return_value = None

        median_query = Mock()
        median_query.filter.return_value = median_query
        median_query.scalar.return_value = None

        mock_db.query.side_effect = [stats_query, median_query]

        result = repository.get_salary_statistics()

        assert result["sample_size"] == 0
        assert result["average"] is None
        assert result["minimum"] is None
        assert result["maximum"] is None
        assert result["median"] is None
        assert result["currency"] is None

    def test_get_total_jobs(self, repository, mock_query):
        """Test getting total jobs count."""
        mock_query.count.return_value = 1000

        result = repository.get_total_jobs()

        assert result == 1000

    def test_count_recent_jobs(self, repository, mock_query):
        """Test counting recent jobs."""
        mock_query.count.return_value = 50

        result = repository.count_recent_jobs(days=7)

        assert result == 50
        mock_query.count.assert_called_once()

    def test_count_jobs_by_source_site(self, repository, mock_query):
        """Test counting jobs from a specific source site."""
        mock_query.count.return_value = 42

        result = repository.count_jobs_by_source_site("linkedin")

        assert result == 42
        mock_query.count.assert_called_once()

    def test_get_jobs_with_company_count(self, repository, mock_query):
        """Test counting jobs with company names."""
        mock_query.count.return_value = 80

        result = repository.get_jobs_with_company_count()

        assert result == 80
        mock_query.count.assert_called_once()

    def test_get_jobs_with_location_count(self, repository, mock_query):
        """Test counting jobs with locations."""
        mock_query.count.return_value = 75

        result = repository.get_jobs_with_location_count()

        assert result == 75
        mock_query.count.assert_called_once()

    def test_get_jobs_with_salary_count(self, repository, mock_query):
        """Test counting jobs with salary data."""
        mock_query.count.return_value = 60

        result = repository.get_jobs_with_salary_count()

        assert result == 60
        mock_query.count.assert_called_once()

    def test_get_jobs_with_employment_type_count(self, repository, mock_query):
        """Test counting jobs with employment type."""
        mock_query.count.return_value = 55

        result = repository.get_jobs_with_employment_type_count()

        assert result == 55
        mock_query.count.assert_called_once()

    def test_get_jobs_with_posted_date_count(self, repository, mock_query):
        """Test counting jobs with posted dates."""
        mock_query.count.return_value = 90

        result = repository.get_jobs_with_posted_date_count()

        assert result == 90
        mock_query.count.assert_called_once()

    def test_get_distinct_source_sites(self, repository, mock_db):
        """Test getting distinct source sites."""
        mock_query = Mock()
        mock_query.distinct.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [
            ("linkedin",),
            ("indeed",),
            ("adzuna",),
        ]

        mock_db.query.return_value = mock_query

        result = repository.get_distinct_source_sites()

        assert result == ["linkedin", "indeed", "adzuna"]
        mock_query.distinct.assert_called_once()
        mock_query.all.assert_called_once()

    def test_get_skill_relationship_count(self, repository, mock_db):
        """Test counting skill-job relationships."""
        mock_query = Mock()
        mock_query.count.return_value = 125

        mock_db.query.return_value = mock_query

        result = repository.get_skill_relationship_count()

        assert result == 125
        mock_query.count.assert_called_once()

    def test_get_jobs_by_source_site(self, repository, mock_query):
        """Test getting jobs from a specific source site."""
        jobs = [Mock(), Mock()]
        mock_query.all.return_value = jobs

        result = repository.get_jobs_by_source_site("linkedin")

        assert result == jobs
        mock_query.all.assert_called_once()
