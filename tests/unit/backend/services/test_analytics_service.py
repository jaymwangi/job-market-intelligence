"""
Unit tests for analytics service.
"""

from unittest.mock import Mock

import pytest

from app.schemas.analytics import (
    DashboardSummaryResponse,
    DatasetSummaryResponse,
    EmploymentDistributionResponse,
    LocationResponse,
    OverviewResponse,
    PostingTrendResponse,
    SalaryByLocationResponse,
    SalaryStatisticsResponse,
    TopCompanyResponse,
    TopSkillResponse,
)
from app.services.analytics_service import AnalyticsService


class TestAnalyticsService:
    """Test suite for AnalyticsService."""

    @pytest.fixture
    def mock_repo(self):
        """Create a mock repository."""
        repo = Mock()
        repo.get_top_skills.return_value = []
        repo.get_top_companies.return_value = []
        repo.get_jobs_by_location.return_value = []
        repo.get_salary_statistics.return_value = {}
        repo.get_employment_type_distribution.return_value = []
        repo.get_salary_by_location.return_value = []
        repo.get_salary_by_company.return_value = []
        repo.get_jobs_posted_by_date.return_value = []
        repo.count_recent_jobs.return_value = 0
        repo.get_salary_distribution.return_value = []
        repo.get_dataset_summary.return_value = {}
        repo.get_total_jobs.return_value = 0
        return repo

    @pytest.fixture
    def service(self, mock_repo):
        return AnalyticsService(mock_repo)

    def test_get_top_skills(self, service, mock_repo):
        """Test getting top skills."""
        mock_repo.get_top_skills.return_value = [
            {"skill": "Python", "count": 450},
            {"skill": "JavaScript", "count": 380},
        ]

        results = service.get_top_skills(limit=2)

        assert len(results) == 2
        assert isinstance(results[0], TopSkillResponse)
        assert results[0].skill == "Python"
        assert results[0].count == 450
        # Use pytest.approx for floating point comparison
        assert results[0].percentage == pytest.approx(54.21686746987952)
        # Or round to 1 decimal
        assert round(results[0].percentage, 1) == 54.2

    def test_get_top_skills_empty(self, service, mock_repo):
        """Test getting top skills with empty results."""
        mock_repo.get_top_skills.return_value = []

        results = service.get_top_skills()

        assert results == []

    def test_get_top_companies(self, service, mock_repo):
        """Test getting top companies."""
        mock_repo.get_top_companies.return_value = [
            {"company": "TechCorp", "job_count": 120},
            {"company": "DataInc", "job_count": 80},
        ]

        results = service.get_top_companies(limit=2)

        assert len(results) == 2
        assert isinstance(results[0], TopCompanyResponse)
        assert results[0].company == "TechCorp"
        assert results[0].job_count == 120
        assert results[0].percentage == 60.0  # 120/200 * 100

    def test_get_jobs_by_location(self, service, mock_repo):
        """Test getting jobs by location."""
        mock_repo.get_jobs_by_location.return_value = [
            {"location": "San Francisco", "job_count": 200},
            {"location": "New York", "job_count": 150},
        ]

        results = service.get_jobs_by_location(limit=2)

        assert len(results) == 2
        assert isinstance(results[0], LocationResponse)
        assert results[0].location == "San Francisco"
        assert results[0].job_count == 200
        # Use pytest.approx for floating point comparison
        assert results[0].percentage == pytest.approx(57.14285714285714)
        # Or round to 1 decimal
        assert round(results[0].percentage, 1) == 57.1

    def test_get_salary_statistics(self, service, mock_repo):
        """Test getting salary statistics."""
        mock_repo.get_salary_statistics.return_value = {
            "average": 135000.0,
            "minimum": 100000.0,
            "maximum": 180000.0,
            "median": 130000.0,
            "sample_size": 500,
            "currency": "USD",
        }

        result = service.get_salary_statistics()

        assert isinstance(result, SalaryStatisticsResponse)
        assert result.average == 135000.0
        assert result.minimum == 100000.0
        assert result.maximum == 180000.0
        assert result.median == 130000.0
        assert result.sample_size == 500
        assert result.currency == "USD"

    def test_get_salary_statistics_empty(self, service, mock_repo):
        """Test getting salary statistics with empty data."""
        mock_repo.get_salary_statistics.return_value = {}

        result = service.get_salary_statistics()

        assert isinstance(result, SalaryStatisticsResponse)
        assert result.average is None
        assert result.sample_size == 0
        assert result.currency == "USD"

    def test_get_employment_types(self, service, mock_repo):
        """Test getting employment type distribution."""
        mock_repo.get_employment_type_distribution.return_value = [
            {"employment_type": "Full-time", "count": 800},
            {"employment_type": "Contract", "count": 200},
        ]

        results = service.get_employment_types()

        assert len(results) == 2
        assert isinstance(results[0], EmploymentDistributionResponse)
        assert results[0].employment_type == "Full-time"
        assert results[0].count == 800
        assert results[0].percentage == 80.0

    def test_get_salary_by_location(self, service, mock_repo):
        """Test getting salary by location."""
        mock_repo.get_salary_by_location.return_value = [
            {
                "location": "San Francisco",
                "average_salary": 145000.0,
                "job_count": 200,
                "min_salary": 110000.0,
                "max_salary": 180000.0,
            }
        ]

        results = service.get_salary_by_location(limit=1)

        assert len(results) == 1
        assert isinstance(results[0], SalaryByLocationResponse)
        assert results[0].location == "San Francisco"
        assert results[0].average_salary == 145000.0
        assert results[0].job_count == 200

    def test_get_posting_trend(self, service, mock_repo):
        """Test getting posting trend."""
        mock_repo.get_jobs_posted_by_date.return_value = [
            {"date": "2026-01-15", "count": 45},
            {"date": "2026-01-16", "count": 50},
            {"date": "2026-01-17", "count": 55},
        ]

        results = service.get_posting_trend(days=3)

        assert len(results) == 3
        assert isinstance(results[0], PostingTrendResponse)
        assert results[0].date == "2026-01-15"
        assert results[0].count == 45
        assert results[0].cumulative == 45
        assert results[1].cumulative == 95
        assert results[2].cumulative == 150

    def test_get_dataset_summary(self, service, mock_repo):
        """Test getting dataset summary."""
        mock_repo.get_dataset_summary.return_value = {
            "total_jobs": 1000,
            "unique_companies": 200,
            "unique_locations": 50,
            "unique_skills": 80,
            "date_range": {"earliest": "2026-01-01", "latest": "2026-01-31"},
            "last_updated": None,
        }

        result = service.get_dataset_summary()

        assert isinstance(result, DatasetSummaryResponse)
        assert result.total_jobs == 1000
        assert result.unique_companies == 200
        assert result.unique_locations == 50
        assert result.unique_skills == 80

    def test_get_overview(self, service, mock_repo):
        """Test getting overview."""
        mock_repo.get_total_jobs.return_value = 1000
        mock_repo.count_recent_jobs.return_value = 50
        mock_repo.get_top_companies.return_value = [{"company": "TechCorp"}]
        mock_repo.get_top_skills.return_value = [{"skill": "Python"}]
        mock_repo.get_salary_statistics.return_value = {"average": 135000.0}

        result = service.get_overview()

        assert isinstance(result, OverviewResponse)
        assert result.total_jobs == 1000
        assert result.recent_jobs == 50
        assert result.top_company == "TechCorp"
        assert result.top_skill == "Python"
        assert result.average_salary == 135000.0

    def test_get_dashboard_summary(self, service, mock_repo):
        """Test getting dashboard summary."""
        mock_repo.get_total_jobs.return_value = 1000
        mock_repo.count_recent_jobs.return_value = 50
        mock_repo.get_top_skills.return_value = [{"skill": "Python", "count": 450}]
        mock_repo.get_top_companies.return_value = [{"company": "TechCorp", "job_count": 120}]
        mock_repo.get_jobs_by_location.return_value = [{"location": "SF", "job_count": 200}]
        mock_repo.get_salary_statistics.return_value = {"average": 135000.0, "sample_size": 500}
        mock_repo.get_employment_type_distribution.return_value = []
        mock_repo.get_jobs_posted_by_date.return_value = []

        result = service.get_dashboard_summary()

        assert isinstance(result, DashboardSummaryResponse)
        assert result.total_jobs == 1000
        assert result.recent_jobs_count == 50
        assert len(result.top_skills) > 0
        assert result.top_skills[0].skill == "Python"
        assert result.top_skills[0].count == 450
        assert result.salary_statistics.average == 135000.0
