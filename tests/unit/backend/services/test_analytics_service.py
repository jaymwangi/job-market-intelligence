"""
Unit tests for analytics service.
"""

from unittest.mock import Mock,patch

import pytest
from datetime import UTC, datetime

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
        mock_repo.get_dataset_summary.return_value = {
            "total_jobs": 1000,
            "unique_companies": 200,
            "unique_locations": 50,
            "unique_skills": 80,
        }
        mock_repo.count_recent_jobs.return_value = 50
        mock_repo.get_top_skills.return_value = [{"skill": "Python", "count": 450}]
        mock_repo.get_top_companies.return_value = [{"company": "TechCorp", "job_count": 120}]
        mock_repo.get_jobs_by_location.return_value = [{"location": "SF", "job_count": 200}]
        mock_repo.get_salary_statistics.return_value = {
            "average": 135000.0,
            "sample_size": 500,
        }
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


    @patch("app.services.analytics_service.logger")
    @patch("app.database.session.get_db")
    def test_get_last_etl_run_returns_na_on_error(
        self, mock_get_db, mock_logger, service
    ):
        mock_get_db.side_effect = RuntimeError("Database unavailable")

        result = service.get_last_etl_run()

        assert result == "N/A"
        mock_logger.error.assert_called_once()

    @patch("app.services.analytics_service.logger")
    @patch("app.database.session.get_db")
    def test_get_last_etl_run_time_returns_none_on_error(
        self, mock_get_db, mock_logger, service
    ):
        mock_get_db.side_effect = RuntimeError("Database unavailable")

        result = service.get_last_etl_run_time()

        assert result is None
        mock_logger.error.assert_called_once()

    @patch("app.services.analytics_service.logger")
    @patch("app.database.session.get_db")
    def test_get_pipeline_status_returns_unknown_on_error(
        self, mock_get_db, mock_logger, service
    ):
        mock_get_db.side_effect = RuntimeError("Database unavailable")

        result = service.get_pipeline_status()

        assert result == "Unknown"
        mock_logger.error.assert_called_once()

    @patch("app.services.analytics_service.logger")
    @patch("app.database.session.get_db")
    def test_get_db_status_returns_unknown_on_error(
        self, mock_get_db, mock_logger, service
    ):
        mock_get_db.side_effect = RuntimeError("Database unavailable")

        result = service.get_db_status()

        assert result == "Unknown"
        mock_logger.error.assert_called_once()

    @patch("app.services.analytics_service.logger")
    def test_get_companies_hiring_count_returns_zero_on_error(
        self, mock_logger, service, mock_repo
    ):
        mock_repo.get_top_companies.side_effect = RuntimeError(
            "Database unavailable"
        )

        result = service.get_companies_hiring_count()

        assert result == 0
        mock_logger.error.assert_called_once()


    @patch("app.repositories.pipeline_run_repository.PipelineRunRepository")
    @patch("app.database.session.get_db")
    def test_get_last_etl_run_success(
        self, mock_get_db, mock_repository, service
    ):
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_repository.return_value.format_last_run_time.return_value = "2h ago"

        result = service.get_last_etl_run()

        assert result == "2h ago"
        mock_repository.return_value.format_last_run_time.assert_called_once()


    @patch("app.repositories.pipeline_run_repository.PipelineRunRepository")
    @patch("app.database.session.get_db")
    def test_get_last_etl_run_time_success(
        self, mock_get_db, mock_repository, service
    ):
        mock_db = Mock()
        expected_time = datetime(2026, 9, 17, 10, 0, tzinfo=UTC)
        mock_get_db.return_value = iter([mock_db])
        mock_repository.return_value.get_last_run_time.return_value = expected_time

        result = service.get_last_etl_run_time()

        assert result == expected_time
        mock_repository.return_value.get_last_run_time.assert_called_once()


    @patch("app.repositories.pipeline_run_repository.PipelineRunRepository")
    @patch("app.database.session.get_db")
    def test_get_pipeline_status_running(
        self, mock_get_db, mock_repository, service
    ):
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_repository.return_value.get_running_run.return_value = {
            "id": 1,
            "status": "running",
        }

        result = service.get_pipeline_status()

        assert result == "Running"


    @patch("app.database.health.check_database_health")
    @patch("app.database.session.get_db")
    def test_get_db_status_operational(
        self, mock_get_db, mock_health, service
    ):
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_health.return_value = {"healthy": True}

        result = service.get_db_status()

        assert result == "Operational"


    def test_get_companies_hiring_count_success(
        self, service, mock_repo
    ):
        mock_repo.get_top_companies.return_value = [
            {"company": "Company A"},
            {"company": "Company B"},
            {"company": "Company C"},
        ]

        result = service.get_companies_hiring_count()

        assert result == 3

    def test_get_salary_by_company(self, service, mock_repo):
        mock_repo.get_salary_by_company.return_value = [
            {
                "company": "Acme Corp",
                "average_salary": 75000,
                "job_count": 10,
                "min_salary": 50000,
                "max_salary": 100000,
            }
        ]

        result = service.get_salary_by_company(limit=5)

        mock_repo.get_salary_by_company.assert_called_once_with(5)
        assert len(result) == 1
        assert result[0].company == "Acme Corp"
        assert result[0].average_salary == 75000
        assert result[0].job_count == 10

    def test_get_recent_jobs_count(self, service, mock_repo):
        mock_repo.count_recent_jobs.return_value = 42

        result = service.get_recent_jobs_count(days=14)

        mock_repo.count_recent_jobs.assert_called_once_with(14)
        assert result == 42

    def test_get_salary_distribution(self, service, mock_repo):
        mock_repo.get_salary_distribution.return_value = [
            {"range": "50k-75k", "count": 10},
            {"range": "75k-100k", "count": 5},
        ]

        result = service.get_salary_distribution()

        mock_repo.get_salary_distribution.assert_called_once_with()
        assert len(result) == 2
        assert result[0].range == "50k-75k"
        assert result[0].count == 10
        assert result[0].percentage == pytest.approx(66.67, rel=1e-2)
        assert result[1].percentage == pytest.approx(33.33, rel=1e-2)

    def test_get_language_distribution(self, service, mock_repo):
        expected = [{"language": "English", "count": 100}]
        mock_repo.get_language_distribution.return_value = expected

        result = service.get_language_distribution()

        mock_repo.get_language_distribution.assert_called_once_with()
        assert result == expected

    def test_get_language_by_country(self, service, mock_repo):
        expected = [{"country": "Kenya", "language": "English", "count": 50}]
        mock_repo.get_language_by_country.return_value = expected

        result = service.get_language_by_country()

        mock_repo.get_language_by_country.assert_called_once_with()
        assert result == expected

    def test_get_english_vs_non_english(self, service, mock_repo):
        expected = {"english": 100, "non_english": 25}
        mock_repo.get_english_vs_non_english.return_value = expected

        result = service.get_english_vs_non_english()

        mock_repo.get_english_vs_non_english.assert_called_once_with()
        assert result == expected

    def test_get_language_salary_stats(self, service, mock_repo):
        expected = [{"language": "English", "average_salary": 75000, "job_count": 20}]
        mock_repo.get_language_salary_stats.return_value = expected

        result = service.get_language_salary_stats()

        mock_repo.get_language_salary_stats.assert_called_once_with()
        assert result == expected

    def test_get_tech_vs_non_tech(self, service, mock_repo):
        expected = {"tech": 80, "non_tech": 40}
        mock_repo.get_tech_vs_non_tech.return_value = expected

        result = service.get_tech_vs_non_tech()

        mock_repo.get_tech_vs_non_tech.assert_called_once_with()
        assert result == expected

    def test_get_technology_category_distribution(self, service, mock_repo):
        expected = [{"category": "Backend", "count": 50}]
        mock_repo.get_technology_category_distribution.return_value = expected

        result = service.get_technology_category_distribution()

        mock_repo.get_technology_category_distribution.assert_called_once_with()
        assert result == expected

    def test_get_tech_by_country(self, service, mock_repo):
        expected = [{"country": "Kenya", "count": 30, "percentage": 60.0}]
        mock_repo.get_tech_by_country.return_value = expected

        result = service.get_tech_by_country()

        mock_repo.get_tech_by_country.assert_called_once_with()
        assert result == expected

    def test_get_tech_skills(self, service, mock_repo):
        expected = [{"skill": "Python", "count": 100}]
        mock_repo.get_tech_skills.return_value = expected

        result = service.get_tech_skills(limit=10)

        mock_repo.get_tech_skills.assert_called_once_with(10)
        assert result == expected

    def test_get_tech_salary_stats(self, service, mock_repo):
        expected = {"average_salary": 85000, "median_salary": 80000}
        mock_repo.get_tech_salary_stats.return_value = expected

        result = service.get_tech_salary_stats()

        mock_repo.get_tech_salary_stats.assert_called_once_with()
        assert result == expected

    def test_get_enriched_top_skills(self, service, mock_repo):
        mock_repo.get_enriched_top_skills.return_value = [
            {"skill": "Python", "count": 100},
            {"skill": "SQL", "count": 80},
        ]

        result = service.get_enriched_top_skills(
            limit=10,
            country_code="KE",
            tech_only=True,
        )

        mock_repo.get_enriched_top_skills.assert_called_once_with(10, "KE", True)
        assert len(result) == 2
        assert result[0].skill == "Python"
        assert result[0].count == 100
        assert result[1].skill == "SQL"
        assert result[1].count == 80

    def test_get_country_distribution(self, service, mock_repo):
        mock_repo.get_country_distribution.return_value = [
            {"country": "Kenya", "count": 50},
            {"country": "Germany", "count": 30},
        ]

        result = service.get_country_distribution()

        mock_repo.get_country_distribution.assert_called_once_with()
        assert len(result) == 2
        assert result[0].country == "Kenya"
        assert result[0].count == 50
        assert result[1].country == "Germany"
        assert result[1].count == 30

    def test_get_technology_distribution(self, service, mock_repo):
        mock_repo.get_technology_distribution.return_value = [
            {"category": "Backend", "count": 60},
            {"category": "Frontend", "count": 40},
        ]

        result = service.get_technology_distribution()

        mock_repo.get_technology_distribution.assert_called_once_with()
        assert len(result) == 2
        assert result[0].category == "Backend"
        assert result[0].count == 60
        assert result[1].category == "Frontend"
        assert result[1].count == 40

    def test_get_enriched_salary_statistics(self, service, mock_repo):
        mock_repo.get_enriched_salary_statistics.return_value = {
            "average_min": 50000,
            "average_max": 100000,
            "minimum": 30000,
            "maximum": 150000,
            "median": 75000,
            "currency": "USD",
        }

        result = service.get_enriched_salary_statistics(
            country_code="KE",
            tech_only=True,
        )

        mock_repo.get_enriched_salary_statistics.assert_called_once_with("KE", True)
        assert result.average_min == 50000
        assert result.average_max == 100000
        assert result.minimum == 30000
        assert result.maximum == 150000
        assert result.median == 75000
        assert result.currency == "USD"