"""
Unit tests for backend analytics schemas.
"""

from datetime import datetime

from app.schemas.analytics import (
    DashboardSummaryResponse,
    DatasetSummaryResponse,
    EmploymentDistributionResponse,
    LocationResponse,
    OverviewResponse,
    PostingTrendResponse,
    SalaryByCompanyResponse,
    SalaryByLocationResponse,
    SalaryDistributionResponse,
    SalaryStatisticsResponse,
    TopCompanyResponse,
    TopSkillResponse,
)


class TestTopSkillResponse:
    """Test suite for TopSkillResponse schema."""

    def test_valid_top_skill(self):
        """Test creating a valid TopSkillResponse."""
        skill = TopSkillResponse(skill="Python", count=450, percentage=25.5)
        assert skill.skill == "Python"
        assert skill.count == 450
        assert skill.percentage == 25.5

    def test_top_skill_without_percentage(self):
        """Test TopSkillResponse without percentage."""
        skill = TopSkillResponse(skill="Python", count=450)
        assert skill.skill == "Python"
        assert skill.count == 450
        assert skill.percentage is None

    def test_top_skill_valid_count(self):
        """Test TopSkillResponse with valid count (no validation on count)."""
        # Pydantic doesn't validate count > 0 unless we add a validator
        skill = TopSkillResponse(skill="Python", count=-5)
        assert skill.count == -5  # It will accept negative values


class TestTopCompanyResponse:
    """Test suite for TopCompanyResponse schema."""

    def test_valid_top_company(self):
        """Test creating a valid TopCompanyResponse."""
        company = TopCompanyResponse(company="TechCorp", job_count=120, percentage=12.5)
        assert company.company == "TechCorp"
        assert company.job_count == 120
        assert company.percentage == 12.5

    def test_top_company_without_percentage(self):
        """Test TopCompanyResponse without percentage."""
        company = TopCompanyResponse(company="TechCorp", job_count=120)
        assert company.company == "TechCorp"
        assert company.job_count == 120
        assert company.percentage is None


class TestLocationResponse:
    """Test suite for LocationResponse schema."""

    def test_valid_location(self):
        """Test creating a valid LocationResponse."""
        location = LocationResponse(location="San Francisco", job_count=200, percentage=20.0)
        assert location.location == "San Francisco"
        assert location.job_count == 200
        assert location.percentage == 20.0


class TestSalaryStatisticsResponse:
    """Test suite for SalaryStatisticsResponse schema."""

    def test_valid_salary_statistics(self):
        """Test creating a valid SalaryStatisticsResponse."""
        stats = SalaryStatisticsResponse(
            average=135000.0,
            minimum=100000.0,
            maximum=180000.0,
            median=130000.0,
            sample_size=500,
            currency="USD",
        )
        assert stats.average == 135000.0
        assert stats.minimum == 100000.0
        assert stats.maximum == 180000.0
        assert stats.median == 130000.0
        assert stats.sample_size == 500
        assert stats.currency == "USD"

    def test_salary_statistics_defaults(self):
        """Test SalaryStatisticsResponse with defaults."""
        stats = SalaryStatisticsResponse()
        assert stats.sample_size == 0
        assert stats.currency is None
        assert stats.average is None

    def test_salary_statistics_valid_sample_size(self):
        """Test SalaryStatisticsResponse with sample_size (no validation)."""
        stats = SalaryStatisticsResponse(sample_size=-10)  # Pydantic doesn't validate this
        assert stats.sample_size == -10


class TestEmploymentDistributionResponse:
    """Test suite for EmploymentDistributionResponse schema."""

    def test_valid_employment_distribution(self):
        """Test creating a valid EmploymentDistributionResponse."""
        emp = EmploymentDistributionResponse(
            employment_type="Full-time", count=800, percentage=80.0
        )
        assert emp.employment_type == "Full-time"
        assert emp.count == 800
        assert emp.percentage == 80.0


class TestSalaryDistributionResponse:
    """Test suite for SalaryDistributionResponse schema."""

    def test_valid_salary_distribution(self):
        """Test creating a valid SalaryDistributionResponse."""
        dist = SalaryDistributionResponse(range="$100k-$120k", count=150, percentage=30.0)
        assert dist.range == "$100k-$120k"
        assert dist.count == 150
        assert dist.percentage == 30.0


class TestPostingTrendResponse:
    """Test suite for PostingTrendResponse schema."""

    def test_valid_posting_trend(self):
        """Test creating a valid PostingTrendResponse."""
        trend = PostingTrendResponse(date="2026-01-15", count=45, cumulative=450)
        assert trend.date == "2026-01-15"
        assert trend.count == 45
        assert trend.cumulative == 450

    def test_posting_trend_without_cumulative(self):
        """Test PostingTrendResponse without cumulative."""
        trend = PostingTrendResponse(date="2026-01-15", count=45)
        assert trend.date == "2026-01-15"
        assert trend.count == 45
        assert trend.cumulative is None


class TestDatasetSummaryResponse:
    """Test suite for DatasetSummaryResponse schema."""

    def test_valid_dataset_summary(self):
        """Test creating a valid DatasetSummaryResponse."""
        summary = DatasetSummaryResponse(
            total_jobs=1000,
            unique_companies=200,
            unique_locations=50,
            unique_skills=80,
            date_range={"min": "2026-01-01", "max": "2026-01-31"},
            last_updated=datetime.now(),
        )
        assert summary.total_jobs == 1000
        assert summary.unique_companies == 200
        assert summary.unique_locations == 50
        assert summary.unique_skills == 80
        assert "min" in summary.date_range
        assert "max" in summary.date_range

    def test_dataset_summary_without_last_updated(self):
        """Test DatasetSummaryResponse without last_updated."""
        summary = DatasetSummaryResponse(
            total_jobs=1000,
            unique_companies=200,
            unique_locations=50,
            unique_skills=80,
            date_range={"min": "2026-01-01", "max": "2026-01-31"},
        )
        assert summary.last_updated is None


class TestSalaryByLocationResponse:
    """Test suite for SalaryByLocationResponse schema."""

    def test_valid_salary_by_location(self):
        """Test creating a valid SalaryByLocationResponse."""
        salary = SalaryByLocationResponse(
            location="San Francisco",
            average_salary=135000.0,
            job_count=200,
            min_salary=100000.0,
            max_salary=180000.0,
        )
        assert salary.location == "San Francisco"
        assert salary.average_salary == 135000.0
        assert salary.job_count == 200
        assert salary.min_salary == 100000.0
        assert salary.max_salary == 180000.0


class TestSalaryByCompanyResponse:
    """Test suite for SalaryByCompanyResponse schema."""

    def test_valid_salary_by_company(self):
        """Test creating a valid SalaryByCompanyResponse."""
        salary = SalaryByCompanyResponse(
            company="TechCorp",
            average_salary=140000.0,
            job_count=50,
            min_salary=110000.0,
            max_salary=170000.0,
        )
        assert salary.company == "TechCorp"
        assert salary.average_salary == 140000.0
        assert salary.job_count == 50


class TestOverviewResponse:
    """Test suite for OverviewResponse schema."""

    def test_valid_overview(self):
        """Test creating a valid OverviewResponse."""
        overview = OverviewResponse(
            total_jobs=1000,
            recent_jobs=50,
            top_company="TechCorp",
            top_skill="Python",
            average_salary=135000.0,
        )
        assert overview.total_jobs == 1000
        assert overview.recent_jobs == 50
        assert overview.top_company == "TechCorp"
        assert overview.top_skill == "Python"
        assert overview.average_salary == 135000.0

    def test_overview_defaults(self):
        """Test OverviewResponse with defaults."""
        overview = OverviewResponse()
        assert overview.total_jobs == 0
        assert overview.recent_jobs == 0
        assert overview.top_company is None
        assert overview.top_skill is None
        assert overview.average_salary is None


class TestDashboardSummaryResponse:
    """Test suite for DashboardSummaryResponse schema."""

    def test_valid_dashboard_summary(self):
        """Test creating a valid DashboardSummaryResponse."""
        dashboard = DashboardSummaryResponse(
            total_jobs=1000,
            recent_jobs_count=50,
            top_companies=[TopCompanyResponse(company="TechCorp", job_count=120)],
            top_locations=[LocationResponse(location="SF", job_count=200)],
            top_skills=[TopSkillResponse(skill="Python", count=450)],
            salary_statistics=SalaryStatisticsResponse(average=135000.0, sample_size=500),
            employment_types=[
                EmploymentDistributionResponse(employment_type="Full-time", count=800)
            ],
            posting_trend=[PostingTrendResponse(date="2026-01-15", count=45)],
        )
        assert dashboard.total_jobs == 1000
        assert len(dashboard.top_companies) == 1
        assert len(dashboard.top_locations) == 1
        assert len(dashboard.top_skills) == 1
        assert dashboard.salary_statistics.average == 135000.0

    def test_dashboard_summary_defaults(self):
        """Test DashboardSummaryResponse with defaults."""
        dashboard = DashboardSummaryResponse()
        assert dashboard.total_jobs == 0
        assert dashboard.top_companies == []
        assert dashboard.top_locations == []
        assert dashboard.top_skills == []
        assert dashboard.employment_types == []
        assert dashboard.posting_trend == []
