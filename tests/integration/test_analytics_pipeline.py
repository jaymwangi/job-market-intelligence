"""PostgreSQL integration tests for the analytics repository."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.skill import Skill
from app.repositories.analytics_repository import AnalyticsRepository


@pytest.fixture
def analytics_data(db_session):
    """Create deterministic PostgreSQL data for analytics integration tests."""
    python = Skill(name="Python")
    sql = Skill(name="SQL")
    docker = Skill(name="Docker")

    tech_gb_1 = Job(
        title="Data Engineer",
        description="Build data pipelines with Python and SQL.",
        company_name="Tech GB",
        location="London",
        salary_min=Decimal("60000.00"),
        salary_max=Decimal("80000.00"),
        salary_currency="GBP",
        source_url="https://example.com/jobs/gb-1",
        source_site="test",
        source_id=f"analytics-{uuid4()}",
        country_code="GB",
        language="en",
        posted_date=datetime(2026, 8, 31, tzinfo=UTC),
        is_tech_role=True,
        technology_category="data",
    )

    tech_gb_2 = Job(
        title="Software Engineer",
        description="Develop backend services with Python.",
        company_name="Tech GB",
        location="Manchester",
        salary_min=Decimal("50000.00"),
        salary_max=Decimal("70000.00"),
        salary_currency="GBP",
        source_url="https://example.com/jobs/gb-2",
        source_site="test",
        source_id=f"analytics-{uuid4()}",
        country_code="GB",
        language="en",
        posted_date=datetime(2026, 8, 31, tzinfo=UTC),
        is_tech_role=True,
        technology_category="backend",
    )

    tech_us = Job(
        title="ML Engineer",
        description="Build machine learning systems with Python and Docker.",
        company_name="Tech US",
        location="New York",
        salary_min=Decimal("90000.00"),
        salary_max=Decimal("120000.00"),
        salary_currency="USD",
        source_url="https://example.com/jobs/us-1",
        source_site="test",
        source_id=f"analytics-{uuid4()}",
        country_code="US",
        language="en",
        posted_date=datetime(2026, 9, 1, tzinfo=UTC),
        is_tech_role=True,
        technology_category="ml_ai",
    )

    non_tech_gb = Job(
        title="Project Manager",
        description="Manage technology projects and delivery.",
        company_name="Business GB",
        location="London",
        salary_min=Decimal("40000.00"),
        salary_max=Decimal("50000.00"),
        salary_currency="GBP",
        source_url="https://example.com/jobs/gb-3",
        source_site="test",
        source_id=f"analytics-{uuid4()}",
        country_code="GB",
        language="en",
        posted_date=datetime(2026, 9, 2, tzinfo=UTC),
        is_tech_role=False,
        technology_category=None,
    )

    db_session.add_all(
        [
            python,
            sql,
            docker,
            tech_gb_1,
            tech_gb_2,
            tech_us,
            non_tech_gb,
        ]
    )
    db_session.flush()

    db_session.add_all(
        [
            JobSkill(
                job_id=tech_gb_1.id,
                skill_id=python.id,
            ),
            JobSkill(
                job_id=tech_gb_1.id,
                skill_id=sql.id,
            ),
            JobSkill(
                job_id=tech_gb_2.id,
                skill_id=python.id,
            ),
            JobSkill(
                job_id=tech_gb_2.id,
                skill_id=sql.id,
            ),
            JobSkill(
                job_id=tech_us.id,
                skill_id=python.id,
            ),
            JobSkill(
                job_id=tech_us.id,
                skill_id=docker.id,
            ),
            JobSkill(
                job_id=non_tech_gb.id,
                skill_id=sql.id,
            ),
        ]
    )

    db_session.flush()

    return {
        "jobs": {
            "tech_gb_1": tech_gb_1,
            "tech_gb_2": tech_gb_2,
            "tech_us": tech_us,
            "non_tech_gb": non_tech_gb,
        },
        "skills": {
            "python": python,
            "sql": sql,
            "docker": docker,
        },
    }


@pytest.fixture
def analytics_repository(db_session):
    """Return AnalyticsRepository backed by the PostgreSQL test session."""
    return AnalyticsRepository(db_session)


class TestTopSkillsIntegration:
    """Integration tests for skill-frequency analytics."""

    def test_get_top_skills_returns_postgresql_results(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Top skills should be aggregated from real job_skill relationships."""
        result = analytics_repository.get_top_skills(limit=10)

        assert result

        skills = {item["skill"]: item["count"] for item in result}

        assert skills["Python"] == 3
        assert skills["SQL"] == 3
        assert skills["Docker"] == 1

    def test_get_top_skills_respects_limit(
        self,
        analytics_repository,
        analytics_data,
    ):
        """The repository should apply the requested result limit."""
        result = analytics_repository.get_top_skills(limit=1)

        assert len(result) == 1
        assert result[0]["count"] == 3
        assert result[0]["skill"] in {"Python", "SQL"}

    def test_get_top_skills_includes_skills_from_all_active_jobs(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Top skills should include relationships from all active jobs."""
        result = analytics_repository.get_top_skills(limit=10)

        sql_result = next(
            item for item in result if item["skill"] == "SQL"
        )

        assert sql_result["count"] == 3


class TestCountryAnalyticsIntegration:
    """Integration tests for country distribution analytics."""

    def test_get_country_distribution_returns_correct_counts(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Country distribution should aggregate active jobs correctly."""
        result = analytics_repository.get_country_distribution()

        assert {"country": "GB", "count": 3} in result
        assert {"country": "US", "count": 1} in result

    def test_get_country_distribution_orders_by_count(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Countries should be returned in descending job-count order."""
        result = analytics_repository.get_country_distribution()

        counts = [item["count"] for item in result]

        assert counts == sorted(counts, reverse=True)
        assert result[0] == {
            "country": "GB",
            "count": 3,
        }


class TestTechnologyAnalyticsIntegration:
    """Integration tests for technology-category analytics."""

    def test_get_technology_distribution_returns_correct_counts(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Technology categories should be aggregated correctly."""
        result = analytics_repository.get_technology_distribution()

        assert {"category": "data", "count": 1} in result
        assert {"category": "backend", "count": 1} in result
        assert {"category": "ml_ai", "count": 1} in result

    def test_get_technology_distribution_excludes_null_categories(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Jobs without a technology category should be excluded."""
        result = analytics_repository.get_technology_distribution()

        categories = {item["category"] for item in result}

        assert None not in categories

    def test_get_technology_distribution_includes_only_tech_roles(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Technology distribution should exclude non-tech jobs."""
        result = analytics_repository.get_technology_distribution()

        total = sum(item["count"] for item in result)

        assert total == 3


class TestSalaryAnalyticsIntegration:
    """Integration tests for PostgreSQL salary statistics."""

    def test_get_salary_statistics_calculates_correct_values(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Salary statistics should use the largest currency group."""
        result = analytics_repository.get_salary_statistics()

        # The repository selects the currency group with the
        # largest sample size.
        #
        # GBP:
        #   salary_min: 60,000 / 50,000 / 40,000
        #   salary_max: 80,000 / 70,000 / 50,000
        #
        # USD:
        #   salary_min: 90,000
        #   salary_max: 120,000
        #
        # Therefore GBP is selected.
        #
        # The repository's median calculation returns 55,000
        # for this dataset.

        assert result["average"] == pytest.approx(50000.0)
        assert result["minimum"] == pytest.approx(40000.0)
        assert result["maximum"] == pytest.approx(80000.0)
        assert float(result["median"]) == pytest.approx(55000.0)
        assert result["sample_size"] == 3
        assert result["currency"] == "GBP"

    def test_get_salary_statistics_ignores_jobs_without_salary(
        self,
        analytics_repository,
        analytics_data,
        db_session,
    ):
        """Jobs with NULL salary values should not affect salary statistics."""
        job_without_salary = Job(
            title="Unpaid Internship",
            description="Internship with no published salary.",
            company_name="No Salary Inc",
            location="London",
            salary_min=None,
            salary_max=None,
            salary_currency=None,
            source_url="https://example.com/jobs/no-salary",
            source_site="test",
            source_id=f"analytics-{uuid4()}",
            country_code="GB",
            language="en",
            posted_date=datetime(2026, 9, 2, tzinfo=UTC),
            is_tech_role=True,
            technology_category="data",
        )

        db_session.add(job_without_salary)
        db_session.flush()

        result = analytics_repository.get_salary_statistics()

        assert result["average"] == pytest.approx(50000.0)
        assert result["minimum"] == pytest.approx(40000.0)
        assert result["maximum"] == pytest.approx(80000.0)
        assert float(result["median"]) == pytest.approx(55000.0)
        assert result["sample_size"] == 3
        assert result["currency"] == "GBP"

    def test_get_salary_statistics_returns_none_when_no_salary_data(
        self,
        analytics_repository,
    ):
        """An empty salary dataset should return the documented empty structure."""
        result = analytics_repository.get_salary_statistics()

        assert result == {
            "average": None,
            "minimum": None,
            "maximum": None,
            "median": None,
            "sample_size": 0,
            "currency": None,
        }


class TestBasicAggregationIntegration:
    """Integration tests for basic analytics aggregations."""

    def test_get_total_jobs_returns_correct_count(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Total jobs should count all active PostgreSQL jobs."""
        result = analytics_repository.get_total_jobs()

        assert result == 4

    def test_get_top_companies_returns_correct_counts(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Company analytics should return exact active-job counts."""
        result = analytics_repository.get_top_companies()

        companies = {
            item["company"]: item["job_count"]
            for item in result
        }

        assert companies["Tech GB"] == 2
        assert companies["Tech US"] == 1
        assert companies["Business GB"] == 1

    def test_get_jobs_by_location_returns_correct_counts(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Location analytics should return exact active-job counts."""
        result = analytics_repository.get_jobs_by_location()

        locations = {
            item["location"]: item["job_count"]
            for item in result
        }

        assert locations["London"] == 2
        assert locations["Manchester"] == 1
        assert locations["New York"] == 1


class TestTechnologySplitIntegration:
    """Integration tests for tech versus non-tech analytics."""

    def test_get_tech_vs_non_tech_returns_correct_values(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Tech/non-tech analytics should match the deterministic dataset."""
        result = analytics_repository.get_tech_vs_non_tech()

        assert result["total_count"] == 4
        assert result["tech_count"] == 3
        assert result["non_tech_count"] == 1
        assert result["tech_percentage"] == pytest.approx(75.0)

    def test_get_tech_by_country_returns_correct_values(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Tech-by-country analytics should calculate exact country ratios."""
        result = analytics_repository.get_tech_by_country()

        countries = {
            item["country"]: item
            for item in result
        }

        assert countries["GB"]["total_count"] == 3
        assert countries["GB"]["tech_count"] == 2
        assert countries["GB"]["tech_percentage"] == pytest.approx(
            2 / 3 * 100
        )

        assert countries["US"]["total_count"] == 1
        assert countries["US"]["tech_count"] == 1
        assert countries["US"]["tech_percentage"] == pytest.approx(
            100.0
        )


class TestEnrichedAnalyticsFilteringIntegration:
    """Integration tests for filtered enriched analytics."""

    def test_get_enriched_top_skills_filters_by_country(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Country filtering should restrict skill aggregation."""
        result = analytics_repository.get_enriched_top_skills(
            country_code="GB"
        )

        skills = {
            item["skill"]: item["count"]
            for item in result
        }

        assert skills["Python"] == 2
        assert skills["SQL"] == 3

    def test_get_enriched_top_skills_filters_to_tech_roles(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Tech-only filtering should exclude non-tech job relationships."""
        result = analytics_repository.get_enriched_top_skills(
            tech_only=True
        )

        skills = {
            item["skill"]: item["count"]
            for item in result
        }

        assert skills["Python"] == 3
        assert skills["SQL"] == 2
        assert skills["Docker"] == 1

    def test_get_enriched_top_skills_combines_country_and_tech_filters(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Country and tech filters should be applied together."""
        result = analytics_repository.get_enriched_top_skills(
            country_code="GB",
            tech_only=True,
        )

        skills = {
            item["skill"]: item["count"]
            for item in result
        }

        assert skills["Python"] == 2
        assert skills["SQL"] == 2


class TestTrendAnalyticsIntegration:
    """Integration tests for time-based analytics."""

    def test_get_jobs_posted_by_date_returns_exact_daily_counts(
        self,
        analytics_repository,
        analytics_data,
    ):
        """Posting trends should aggregate jobs into exact calendar dates."""
        result = analytics_repository.get_jobs_posted_by_date(days=30)

        counts = {
            item["date"]: item["count"]
            for item in result
        }

        assert counts["2026-08-31"] == 2
        assert counts["2026-09-01"] == 1
        assert counts["2026-09-02"] == 1


class TestEmptyAnalyticsIntegration:
    """Integration tests for empty active-job analytics."""

    def test_empty_dataset_returns_zero_or_empty_analytics(
        self,
        analytics_repository,
    ):
        """Analytics should return safe empty results when no jobs exist."""
        assert analytics_repository.get_total_jobs() == 0
        assert analytics_repository.get_country_distribution() == []

        result = analytics_repository.get_tech_vs_non_tech()

        assert result["total_count"] == 0
        assert result["tech_count"] == 0
        assert result["non_tech_count"] == 0