"""Analytics service layer for business logic and orchestration."""

from typing import List, Optional
from datetime import datetime
from app.repositories.analytics_repository import AnalyticsRepository
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
    # Sprint 6.6: New schemas
    SkillCount,
    CountryDistribution,
    TechnologyDistribution,
    SalaryStatistics,
)
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service layer for analytics orchestration."""

    def __init__(self, repo: AnalyticsRepository):
        self.repo = repo

    # ============================================================
    # Existing Methods (unchanged)
    # ============================================================

    def get_top_skills(self, limit: int = 10) -> list[TopSkillResponse]:
        """Get top skills with counts and percentages."""
        results = self.repo.get_top_skills(limit)
        total = sum(r.get("count", 0) for r in results) if results else 1

        return [
            TopSkillResponse(
                skill=r.get("skill", ""),
                count=r.get("count", 0),
                percentage=(r.get("count", 0) / total * 100) if total > 0 else 0,
            )
            for r in results
        ]

    def get_top_companies(self, limit: int = 10) -> list[TopCompanyResponse]:
        """Get top companies with job counts and percentages."""
        results = self.repo.get_top_companies(limit)
        total = sum(r.get("job_count", 0) for r in results) if results else 1

        return [
            TopCompanyResponse(
                company=r.get("company", ""),
                job_count=r.get("job_count", 0),
                percentage=(r.get("job_count", 0) / total * 100) if total > 0 else 0,
            )
            for r in results
        ]

    def get_jobs_by_location(self, limit: int = 10) -> list[LocationResponse]:
        """Get job distribution by location with percentages."""
        results = self.repo.get_jobs_by_location(limit)
        total = sum(r.get("job_count", 0) for r in results) if results else 1

        return [
            LocationResponse(
                location=r.get("location", "Unknown"),
                job_count=r.get("job_count", 0),
                percentage=(r.get("job_count", 0) / total * 100) if total > 0 else 0,
            )
            for r in results
        ]

    def get_salary_statistics(self) -> SalaryStatisticsResponse:
        """Get aggregate salary statistics."""
        stats = self.repo.get_salary_statistics()

        return SalaryStatisticsResponse(
            average=stats.get("average"),
            minimum=stats.get("minimum"),
            maximum=stats.get("maximum"),
            median=stats.get("median"),
            sample_size=stats.get("sample_size", 0),
            currency=stats.get("currency", "USD"),
        )

    def get_employment_types(self) -> list[EmploymentDistributionResponse]:
        """Get employment type distribution with percentages."""
        results = self.repo.get_employment_type_distribution()
        total = sum(r.get("count", 0) for r in results) if results else 1

        return [
            EmploymentDistributionResponse(
                employment_type=r.get("employment_type", "Unknown"),
                count=r.get("count", 0),
                percentage=(r.get("count", 0) / total * 100) if total > 0 else 0,
            )
            for r in results
        ]

    def get_salary_by_location(self, limit: int = 10) -> list[SalaryByLocationResponse]:
        """Get salary statistics by location."""
        results = self.repo.get_salary_by_location(limit)

        return [
            SalaryByLocationResponse(
                location=r.get("location", "Unknown"),
                average_salary=r.get("average_salary"),
                job_count=r.get("job_count", 0),
                min_salary=r.get("min_salary"),
                max_salary=r.get("max_salary"),
            )
            for r in results
        ]

    def get_salary_by_company(self, limit: int = 10) -> list[SalaryByCompanyResponse]:
        """Get salary statistics by company."""
        results = self.repo.get_salary_by_company(limit)

        return [
            SalaryByCompanyResponse(
                company=r.get("company", "Unknown"),
                average_salary=r.get("average_salary"),
                job_count=r.get("job_count", 0),
                min_salary=r.get("min_salary"),
                max_salary=r.get("max_salary"),
            )
            for r in results
        ]

    def get_posting_trend(self, days: int = 30) -> list[PostingTrendResponse]:
        """Get job posting trend over time with cumulative counts."""
        results = self.repo.get_jobs_posted_by_date(days)
        cumulative = 0

        trend = []
        for r in results:
            cumulative += r.get("count", 0)
            trend.append(
                PostingTrendResponse(
                    date=r.get("date", ""),
                    count=r.get("count", 0),
                    cumulative=cumulative,
                )
            )
        return trend

    def get_recent_jobs_count(self, days: int = 7) -> int:
        """Get count of recently posted jobs."""
        return self.repo.count_recent_jobs(days)

    def get_salary_distribution(self) -> list[SalaryDistributionResponse]:
        """Get salary distribution by ranges with percentages."""
        results = self.repo.get_salary_distribution()
        total = sum(r.get("count", 0) for r in results) if results else 1

        return [
            SalaryDistributionResponse(
                range=r.get("range", ""),
                count=r.get("count", 0),
                percentage=(r.get("count", 0) / total * 100) if total > 0 else 0,
            )
            for r in results
        ]

    def get_dataset_summary(self) -> DatasetSummaryResponse:
        """Get comprehensive dataset summary."""
        summary = self.repo.get_dataset_summary()

        return DatasetSummaryResponse(
            total_jobs=summary.get("total_jobs", 0),
            unique_companies=summary.get("unique_companies", 0),
            unique_locations=summary.get("unique_locations", 0),
            unique_skills=summary.get("unique_skills", 0),
            date_range=summary.get("date_range", {"earliest": None, "latest": None}),
            last_updated=summary.get("last_updated"),
        )

    def get_overview(self) -> OverviewResponse:
        """Get lightweight overview for general API consumers."""
        total_jobs = self.repo.get_total_jobs()
        recent_jobs = self.repo.count_recent_jobs(7)
        top_company = self.repo.get_top_companies(1)
        top_skill = self.repo.get_top_skills(1)
        salary_stats = self.repo.get_salary_statistics()

        return OverviewResponse(
            total_jobs=total_jobs,
            recent_jobs=recent_jobs,
            top_company=top_company[0].get("company") if top_company else None,
            top_skill=top_skill[0].get("skill") if top_skill else None,
            average_salary=salary_stats.get("average"),
        )

    def get_dashboard_summary(self) -> DashboardSummaryResponse:
        """Get comprehensive dashboard summary for Streamlit."""
        # Get dataset summary for unique counts
        dataset_summary = self.repo.get_dataset_summary()
        
        # Get recent jobs count
        recent_jobs_count = self.repo.count_recent_jobs(7)

        return DashboardSummaryResponse(
            # Core metrics
            total_jobs=dataset_summary.get("total_jobs", 0),
            recent_jobs_count=recent_jobs_count,
            
            # Unique counts from dataset summary
            unique_companies=dataset_summary.get("unique_companies", 0),
            unique_locations=dataset_summary.get("unique_locations", 0),
            unique_skills=dataset_summary.get("unique_skills", 0),
            
            # Top lists
            top_companies=self.get_top_companies(10),
            top_locations=self.get_jobs_by_location(10),
            top_skills=self.get_top_skills(10),
            
            # Salary statistics
            salary_statistics=self.get_salary_statistics(),
            
            # Employment distribution
            employment_types=self.get_employment_types(),
            
            # Time series
            posting_trend=self.get_posting_trend(30),
        )

    # ============================================================
    # Sprint 6.6: Language Analytics
    # ============================================================

    def get_language_distribution(self) -> list[dict[str, str | int]]:
        """Get job distribution by language."""
        logger.debug("Fetching language distribution")
        return self.repo.get_language_distribution()

    def get_language_by_country(self) -> list[dict[str, str | int]]:
        """Get language distribution by country."""
        logger.debug("Fetching language by country")
        return self.repo.get_language_by_country()

    def get_english_vs_non_english(self) -> dict[str, int | float]:
        """Get English vs non-English job distribution."""
        logger.debug("Fetching English vs non-English distribution")
        return self.repo.get_english_vs_non_english()

    def get_language_salary_stats(self) -> list[dict[str, str | float | int | None]]:
        """Get salary statistics by language."""
        logger.debug("Fetching salary by language")
        return self.repo.get_language_salary_stats()

    # ============================================================
    # Sprint 6.6: Technology Analytics
    # ============================================================

    def get_tech_vs_non_tech(self) -> dict[str, int | float]:
        """Get tech vs non-tech job distribution."""
        logger.debug("Fetching tech vs non-tech distribution")
        return self.repo.get_tech_vs_non_tech()

    def get_technology_category_distribution(self) -> list[dict[str, str | int]]:
        """Get distribution of technology categories."""
        logger.debug("Fetching technology category distribution")
        return self.repo.get_technology_category_distribution()

    def get_tech_by_country(self) -> list[dict[str, str | int | float]]:
        """Get technology role distribution by country."""
        logger.debug("Fetching tech by country")
        return self.repo.get_tech_by_country()

    def get_tech_skills(self, limit: int = 20) -> list[dict[str, str | int]]:
        """Get most common skills in technology roles."""
        logger.debug("Fetching tech skills (limit=%d)", limit)
        return self.repo.get_tech_skills(limit)

    def get_tech_salary_stats(self) -> dict[str, float | int | None]:
        """Get salary statistics for technology roles."""
        logger.debug("Fetching tech salary statistics")
        return self.repo.get_tech_salary_stats()

    # ============================================================
    # Sprint 6.6: Enriched Combined Analytics (RESTful Resources)
    # ============================================================

    def get_enriched_top_skills(
        self,
        limit: int = 20,
        country_code: str | None = None,
        tech_only: bool = False,
    ) -> list[SkillCount]:
        """
        Get skills with frequency counts and optional filters.

        Args:
            limit: Number of skills to return
            country_code: Optional country filter
            tech_only: Whether to filter to tech roles only

        Returns:
            List of SkillCount objects
        """
        logger.debug(
            "Fetching enriched skills (limit=%d%s%s)",
            limit,
            f", country={country_code}" if country_code else "",
            ", tech_only=True" if tech_only else "",
        )
        results = self.repo.get_enriched_top_skills(limit, country_code, tech_only)
        return [SkillCount(skill=r["skill"], count=r["count"]) for r in results]

    def get_country_distribution(self) -> list[CountryDistribution]:
        """
        Get job distribution by country.

        Returns:
            List of CountryDistribution objects
        """
        logger.debug("Fetching country distribution")
        results = self.repo.get_country_distribution()
        return [CountryDistribution(country=r["country"], count=r["count"]) for r in results]

    def get_technology_distribution(self) -> list[TechnologyDistribution]:
        """
        Get distribution of technology categories.

        Returns:
            List of TechnologyDistribution objects
        """
        logger.debug("Fetching technology distribution")
        results = self.repo.get_technology_distribution()
        return [TechnologyDistribution(category=r["category"], count=r["count"]) for r in results]

    def get_enriched_salary_statistics(
        self,
        country_code: str | None = None,
        tech_only: bool = False,
    ) -> SalaryStatistics:
        """
        Get salary statistics with optional filters.

        Args:
            country_code: Optional country filter
            tech_only: Whether to filter to tech roles only

        Returns:
            SalaryStatistics object
        """
        logger.debug(
            "Fetching enriched salary statistics%s%s",
            f" for country {country_code}" if country_code else "",
            " (tech only)" if tech_only else "",
        )
        stats = self.repo.get_enriched_salary_statistics(country_code, tech_only)
        return SalaryStatistics(
            average_min=stats.get("average_min"),
            average_max=stats.get("average_max"),
            minimum=stats.get("minimum"),
            maximum=stats.get("maximum"),
            median=stats.get("median"),
            currency=stats.get("currency", "USD"),
        )

    # ============================================================
    # ETL Status Methods for Dashboard Overview
    # ============================================================

    def get_last_etl_run(self) -> str:
        """
        Get formatted last ETL run time.
        Returns string like "2 hours ago" or "No runs yet".
        """
        try:
            from app.repositories.pipeline_run_repository import PipelineRunRepository
            from app.database.session import get_db
            
            db = next(get_db())
            repo = PipelineRunRepository(db)
            return repo.format_last_run_time()
        except Exception as e:
            logger.error(f"Failed to get last ETL run: {e}")
            return "N/A"

    def get_last_etl_run_time(self) -> Optional[datetime]:
        """
        Get the actual datetime of the last ETL run.
        Returns datetime or None.
        """
        try:
            from app.repositories.pipeline_run_repository import PipelineRunRepository
            from app.database.session import get_db
            
            db = next(get_db())
            repo = PipelineRunRepository(db)
            return repo.get_last_run_time()
        except Exception as e:
            logger.error(f"Failed to get last ETL run time: {e}")
            return None

    def get_pipeline_status(self) -> str:
        """
        Get current pipeline status.
        Returns "Running", "Idle", or "Unknown".
        """
        try:
            from app.repositories.pipeline_run_repository import PipelineRunRepository
            from app.database.session import get_db
            
            db = next(get_db())
            repo = PipelineRunRepository(db)
            running = repo.get_running_run()
            return "Running" if running else "Idle"
        except Exception as e:
            logger.error(f"Failed to get pipeline status: {e}")
            return "Unknown"

    def get_db_status(self) -> str:
        """
        Get database status.
        Returns "Operational", "Degraded", or "Unknown".
        """
        try:
            from app.database.health import check_database_health
            from app.database.session import get_db
            
            db = next(get_db())
            result = check_database_health(db)
            return "Operational" if result.get("healthy") else "Degraded"
        except Exception as e:
            logger.error(f"Failed to get database status: {e}")
            return "Unknown"

    def get_companies_hiring_count(self) -> int:
        """
        Get count of companies currently hiring.
        """
        try:
            # Use the existing repo method
            companies = self.repo.get_top_companies(limit=1000)
            return len(companies) if companies else 0
        except Exception as e:
            logger.error(f"Failed to get companies hiring count: {e}")
            return 0