"""Analytics service with full transformation pipeline."""

import logging
from typing import Any, Optional
from datetime import datetime

from api.client import APIClient
from mappers.analytics_mapper import AnalyticsMapper
from schemas.analytics import (
    DashboardSummary,
    EmploymentType,
    LocationAnalytics,
    PostingTrend,
    SalaryDistribution,
    SalaryStatistics,
    TopCompany,
    TopSkill,
)
from schemas.chart_data import (
    BarChartData,
    DonutChartData,
    HistogramData,
    HorizontalBarChartData,
    LineChartData,
    MetricCardData,
    PieChartData,
)
from services.base import BaseService
from utils.cache import CacheManager, cached

logger = logging.getLogger(__name__)


class AnalyticsService(BaseService):
    """
    Analytics service with full transformation pipeline.

    The service owns the entire transformation chain:
    1. Fetch data from API
    2. Validate and normalize to domain models
    3. Transform to chart models via mapper
    4. Return presentation-ready data

    Sprint 6.6 adds:
    - Language analytics methods
    - Technology analytics methods
    - Enriched combined analytics methods
    """

    def __init__(self, api_client: APIClient, cache_manager: CacheManager | None = None):
        super().__init__(api_client, cache_manager)
        self.mapper = AnalyticsMapper()

    # ========== Chart Model Methods (Presentation-Ready) ==========

    @cached(ttl=300)
    def get_dashboard_metrics(self) -> list[MetricCardData]:
        """Get presentation-ready dashboard metrics."""
        try:
            summary = self._fetch_dashboard_summary()
            return self.mapper.to_metric_cards(summary)
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {e}")
            return []

    @cached(ttl=600)
    def get_skills_chart(self, limit: int = 15) -> HorizontalBarChartData:
        """Get presentation-ready skills chart."""
        try:
            skills = self._fetch_top_skills(limit)
            return self.mapper.to_horizontal_bar_chart(
                data=skills,
                title="Most In-Demand Skills",
                label_field="skill",
                value_field="count",
                x_label="Job Count",
                y_label="Skill",
                color="#ff7f0e",
                show_values=True,
            )
        except Exception as e:
            logger.error(f"Failed to get skills chart: {e}")
            return HorizontalBarChartData(title="Most In-Demand Skills", x_values=[], y_values=[])

    @cached(ttl=600)
    def get_skills_distribution_chart(self, limit: int = 8) -> PieChartData:
        """Get presentation-ready skills distribution."""
        try:
            skills = self._fetch_top_skills(limit)
            return self.mapper.to_pie_chart(
                data=skills,
                title="Skill Distribution",
                label_field="skill",
                value_field="count",
                show_percentage=True,
            )
        except Exception as e:
            logger.error(f"Failed to get skills distribution: {e}")
            return PieChartData(title="Skill Distribution", labels=[], values=[])

    @cached(ttl=600)
    def get_companies_chart(self, limit: int = 15) -> HorizontalBarChartData:
        """Get presentation-ready companies chart."""
        try:
            companies = self._fetch_top_companies(limit)
            return self.mapper.to_horizontal_bar_chart(
                data=companies,
                title="Top Companies by Job Postings",
                label_field="company",
                value_field="job_count",
                x_label="Number of Jobs",
                y_label="Company",
                color="#1f77b4",
                show_values=True,
            )
        except Exception as e:
            logger.error(f"Failed to get companies chart: {e}")
            return HorizontalBarChartData(
                title="Top Companies by Job Postings", x_values=[], y_values=[]
            )

    @cached(ttl=600)
    def get_companies_distribution_chart(self, limit: int = 8) -> DonutChartData:
        """Get presentation-ready companies distribution."""
        try:
            companies = self._fetch_top_companies(limit)
            return self.mapper.to_donut_chart(
                data=companies,
                title="Company Distribution",
                label_field="company",
                value_field="job_count",
                show_percentage=True,
                hole_size=0.4,
            )
        except Exception as e:
            logger.error(f"Failed to get companies distribution: {e}")
            return DonutChartData(title="Company Distribution", labels=[], values=[])

    @cached(ttl=600)
    def get_locations_chart(self, limit: int = 15) -> HorizontalBarChartData:
        """Get presentation-ready locations chart."""
        try:
            locations = self._fetch_jobs_by_location(limit)
            return self.mapper.to_horizontal_bar_chart(
                data=locations,
                title="Top Locations by Job Count",
                label_field="location",
                value_field="job_count",
                x_label="Number of Jobs",
                y_label="Location",
                color="#2ca02c",
                show_values=True,
            )
        except Exception as e:
            logger.error(f"Failed to get locations chart: {e}")
            return HorizontalBarChartData(
                title="Top Locations by Job Count", x_values=[], y_values=[]
            )

    @cached(ttl=900)
    def get_salary_statistics(self) -> SalaryStatistics | None:
        """Get salary statistics (domain model)."""
        try:
            return self._fetch_salary_statistics()
        except Exception as e:
            logger.error(f"Failed to get salary statistics: {e}")
            return None

    @cached(ttl=900)
    def get_salary_distribution_chart(self) -> HistogramData:
        """Get presentation-ready salary distribution."""
        try:
            distribution = self._fetch_salary_distribution()
            return self.mapper.to_salary_histogram(distribution)
        except Exception as e:
            logger.error(f"Failed to get salary distribution: {e}")
            return HistogramData(title="Salary Distribution", bins=[], counts=[])

    @cached(ttl=900)
    def get_salary_by_location_chart(self, limit: int = 10) -> BarChartData:
        """Get presentation-ready salary by location."""
        try:
            salary_locations = self._fetch_salary_by_location(limit)
            return self.mapper.to_bar_chart(
                data=salary_locations,
                title="Average Salary by Location",
                label_field="location",
                value_field="average_salary",
                x_label="Location",
                y_label="Average Salary (USD)",
                color="#d62728",
                show_values=True,
            )
        except Exception as e:
            logger.error(f"Failed to get salary by location: {e}")
            return BarChartData(title="Average Salary by Location", x_values=[], y_values=[])

    @cached(ttl=600)
    def get_employment_types_chart(self) -> DonutChartData:
        """Get presentation-ready employment types distribution."""
        try:
            employment_types = self._fetch_employment_types()
            return self.mapper.to_donut_chart(
                data=employment_types,
                title="Employment Type Distribution",
                label_field="employment_type",
                value_field="count",
                show_percentage=True,
                hole_size=0.4,
            )
        except Exception as e:
            logger.error(f"Failed to get employment types: {e}")
            return DonutChartData(title="Employment Type Distribution", labels=[], values=[])

    @cached(ttl=600)
    def get_employment_types_bar_chart(self) -> BarChartData:
        """Get presentation-ready employment types bar chart."""
        try:
            employment_types = self._fetch_employment_types()
            return self.mapper.to_bar_chart(
                data=employment_types,
                title="Employment Type Counts",
                label_field="employment_type",
                value_field="count",
                x_label="Employment Type",
                y_label="Number of Jobs",
                color="#9467bd",
                show_values=True,
            )
        except Exception as e:
            logger.error(f"Failed to get employment types bar chart: {e}")
            return BarChartData(title="Employment Type Counts", x_values=[], y_values=[])

    @cached(ttl=300)
    def get_posting_trend_chart(self, days: int = 30) -> LineChartData:
        """Get presentation-ready posting trend chart."""
        try:
            trends = self._fetch_posting_trend(days)
            return self.mapper.to_line_chart(
                data=trends,
                title=f"Job Postings Over Time (Last {days} Days)",
                x_field="date",
                y_field="cumulative",
                x_label="Date",
                y_label="Cumulative Jobs",
                fill_area=True,
                show_markers=True,
            )
        except Exception as e:
            logger.error(f"Failed to get posting trend: {e}")
            return LineChartData(title="Job Postings Over Time", x_values=[], y_values=[])

    @cached(ttl=300)
    def get_daily_posting_trend_chart(self, days: int = 30) -> LineChartData:
        """Get presentation-ready daily posting trend chart."""
        try:
            trends = self._fetch_posting_trend(days)
            return self.mapper.to_line_chart(
                data=trends,
                title="Daily Job Postings",
                x_field="date",
                y_field="count",
                x_label="Date",
                y_label="Daily Jobs",
                fill_area=False,
                show_markers=True,
            )
        except Exception as e:
            logger.error(f"Failed to get daily posting trend: {e}")
            return LineChartData(title="Daily Job Postings", x_values=[], y_values=[])

    # ============================================================
    # Sprint 6.6: Language Analytics
    # ============================================================

    @cached(ttl=600)
    def get_language_distribution(self) -> list[dict[str, Any]]:
        """
        Get job distribution by language.

        Returns:
            List of dicts with language and count
        """
        try:
            response = self.api_client.get("/api/v1/analytics/language/distribution")
            if isinstance(response, list):
                return response
            if isinstance(response, dict) and "data" in response:
                return response.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get language distribution: {e}")
            return []

    @cached(ttl=600)
    def get_language_by_country(self) -> list[dict[str, Any]]:
        """
        Get language distribution by country.

        Returns:
            List of dicts with country, language, and count
        """
        try:
            response = self.api_client.get("/api/v1/analytics/language/by-country")
            if isinstance(response, list):
                return response
            if isinstance(response, dict) and "data" in response:
                return response.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get language by country: {e}")
            return []

    @cached(ttl=300)
    def get_english_vs_non_english(self) -> dict[str, Any]:
        """
        Get English vs non-English job distribution.

        Returns:
            Dict with english_count, non_english_count, total_count, english_percentage
        """
        try:
            response = self.api_client.get("/api/v1/analytics/language/english-vs-non-english")
            if isinstance(response, dict):
                return response
            return {}
        except Exception as e:
            logger.error(f"Failed to get English vs non-English: {e}")
            return {}

    @cached(ttl=900)
    def get_language_salary_stats(self) -> list[dict[str, Any]]:
        """
        Get salary statistics by language.

        Returns:
            List of dicts with language, average_salary, count, min, max
        """
        try:
            response = self.api_client.get("/api/v1/analytics/language/salary")
            if isinstance(response, list):
                return response
            if isinstance(response, dict) and "data" in response:
                return response.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get language salary stats: {e}")
            return []

    # ============================================================
    # Sprint 6.6: Technology Analytics
    # ============================================================

    @cached(ttl=300)
    def get_tech_vs_non_tech(self) -> dict[str, Any]:
        """
        Get tech vs non-tech job distribution.

        Returns:
            Dict with tech_count, non_tech_count, total_count, tech_percentage
        """
        try:
            response = self.api_client.get("/api/v1/analytics/tech/vs-non-tech")
            if isinstance(response, dict):
                return response
            return {}
        except Exception as e:
            logger.error(f"Failed to get tech vs non-tech: {e}")
            return {}

    @cached(ttl=600)
    def get_tech_category_distribution(self) -> list[dict[str, Any]]:
        """
        Get distribution of technology categories.

        Returns:
            List of dicts with category and count
        """
        try:
            response = self.api_client.get("/api/v1/analytics/tech/category-distribution")
            if isinstance(response, list):
                return response
            if isinstance(response, dict) and "data" in response:
                return response.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get tech category distribution: {e}")
            return []

    @cached(ttl=600)
    def get_tech_by_country(self) -> list[dict[str, Any]]:
        """
        Get technology role distribution by country.

        Returns:
            List of dicts with country, total_count, tech_count, tech_percentage
        """
        try:
            response = self.api_client.get("/api/v1/analytics/tech/by-country")
            if isinstance(response, list):
                return response
            if isinstance(response, dict) and "data" in response:
                return response.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get tech by country: {e}")
            return []

    @cached(ttl=600)
    def get_tech_skills(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Get most common skills in technology roles.

        Args:
            limit: Number of skills to return

        Returns:
            List of dicts with skill and count
        """
        try:
            response = self.api_client.get(
                "/api/v1/analytics/tech/skills",
                params={"limit": limit}
            )
            if isinstance(response, list):
                return response
            if isinstance(response, dict) and "data" in response:
                return response.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get tech skills: {e}")
            return []

    @cached(ttl=900)
    def get_tech_salary_stats(self) -> dict[str, Any]:
        """
        Get salary statistics for technology roles.

        Returns:
            Dict with average, min, max, median, sample_size
        """
        try:
            response = self.api_client.get("/api/v1/analytics/tech/salary")
            if isinstance(response, dict):
                return response
            return {}
        except Exception as e:
            logger.error(f"Failed to get tech salary stats: {e}")
            return {}
        
    # ============================================================
    # Sprint 6.6: Enriched Combined Analytics (RESTful Resources)
    # ============================================================

    @cached(ttl=600)
    def get_enriched_top_skills(
        self,
        limit: int = 20,
        country_code: Optional[str] = None,
        tech_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Get top skills with frequency counts from enriched data."""
        try:
            params: dict[str, str] = {"limit": str(limit)}
            if country_code:
                params["country_code"] = country_code
            if tech_only:
                params["tech_only"] = "true"
            response = self.api_client.get("/api/v1/analytics/enriched/skills", params=params)
            if isinstance(response, list):
                return response
            if isinstance(response, dict) and "data" in response:
                return response.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get enriched top skills: {e}")
            return []

    @cached(ttl=600)
    def get_country_distribution(self) -> list[dict[str, Any]]:
        """Get job distribution by country from enriched data."""
        try:
            response = self.api_client.get("/api/v1/analytics/enriched/countries")
            if isinstance(response, list):
                return response
            if isinstance(response, dict) and "data" in response:
                return response.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get country distribution: {e}")
            return []

    @cached(ttl=600)
    def get_technology_distribution(self) -> list[dict[str, Any]]:
        """Get technology category distribution from enriched data."""
        try:
            response = self.api_client.get("/api/v1/analytics/enriched/technology")
            if isinstance(response, list):
                return response
            if isinstance(response, dict) and "data" in response:
                return response.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get technology distribution: {e}")
            return []

    @cached(ttl=900)
    def get_enriched_salary(
        self,
        country_code: Optional[str] = None,
        tech_only: bool = False,
    ) -> dict[str, Any]:
        """Get enriched salary statistics with optional filters."""
        try:
            params: dict[str, str] = {}
            if country_code:
                params["country_code"] = country_code
            if tech_only:
                params["tech_only"] = "true"
            response = self.api_client.get("/api/v1/analytics/enriched/salary", params=params)
            if isinstance(response, dict):
                return response
            return {}
        except Exception as e:
            logger.error(f"Failed to get enriched salary: {e}")
            return {}

    # ============================================================
    # ETL Status Methods - For Dashboard Overview
    # ============================================================

    @cached(ttl=60)  # Cache for 60 seconds
    def get_last_etl_run(self) -> str:
        """
        Get formatted last ETL run time.
        Returns string like "2 hours ago" or "No runs yet".
        """
        # First try the API endpoint
        try:
            response = self.api_client.get("/api/v1/analytics/etl/last-run")
            if response and 'last_run' in response:
                return response['last_run']
        except Exception as e:
            logger.debug(f"API endpoint /analytics/etl/last-run not available: {e}")

        # Fallback: Direct database access via app modules
        try:
            import sys
            import os
            # Add project root to path if needed
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from app.repositories.pipeline_run_repository import PipelineRunRepository
            from app.database.session import get_db
            
            db = next(get_db())
            repo = PipelineRunRepository(db)
            return repo.format_last_run_time()
        except ImportError as e:
            logger.error(f"Failed to import app modules: {e}")
            return "N/A"
        except Exception as e:
            logger.error(f"Failed to get last ETL run: {e}")
            return "N/A"

    @cached(ttl=60)
    def get_last_etl_run_time(self) -> Optional[datetime]:
        """
        Get the actual datetime of the last ETL run.
        Returns datetime or None.
        """
        # First try the API endpoint
        try:
            response = self.api_client.get("/api/v1/analytics/etl/last-run-time")
            if response and 'last_run_time' in response and response['last_run_time']:
                return datetime.fromisoformat(response['last_run_time'])
        except Exception as e:
            logger.debug(f"API endpoint not available: {e}")

        # Fallback: Direct database access
        try:
            import sys
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from app.repositories.pipeline_run_repository import PipelineRunRepository
            from app.database.session import get_db
            
            db = next(get_db())
            repo = PipelineRunRepository(db)
            return repo.get_last_run_time()
        except Exception as e:
            logger.error(f"Failed to get last ETL run time: {e}")
            return None

    @cached(ttl=60)
    def get_pipeline_status(self) -> str:
        """
        Get current pipeline status.
        Returns "Running", "Idle", or "Unknown".
        """
        # First try the API endpoint
        try:
            response = self.api_client.get("/api/v1/analytics/etl/status")
            if response and 'status' in response:
                return response['status']
        except Exception as e:
            logger.debug(f"API endpoint not available: {e}")

        # Fallback: Direct database access
        try:
            import sys
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from app.repositories.pipeline_run_repository import PipelineRunRepository
            from app.database.session import get_db
            
            db = next(get_db())
            repo = PipelineRunRepository(db)
            running = repo.get_running_run()
            return "Running" if running else "Idle"
        except Exception as e:
            logger.error(f"Failed to get pipeline status: {e}")
            return "Unknown"
        
    @cached(ttl=60)
    def get_db_status(self) -> str:
        """
        Get database status from backend API.
        Returns "Operational", "Degraded", or "Unknown".
        """
        try:
            # If base_url doesn't include /api/v1, use full path
            response = self.api_client.get("/api/v1/health/db")
            
            if response:
                status = response.get('status', '')
                if status.lower() in ['healthy', 'ok']:
                    return "Operational"
                elif status.lower() == 'unhealthy':
                    return "Degraded"
            return "Unknown"
                
        except Exception as e:
            logger.error(f"Failed to fetch DB status from API: {e}")
            return "Unknown"

    @cached(ttl=600)
    def get_companies_hiring_count(self) -> int:
        """
        Get count of companies currently hiring.
        """
        try:
            response = self.api_client.get("/api/v1/analytics/companies/count")
            if response and 'count' in response:
                return response.get('count', 0)
        except Exception as e:
            logger.debug(f"API endpoint not available: {e}")

        # Fallback: Use top companies
        try:
            companies = self._fetch_top_companies(limit=1000)
            return len(companies)
        except Exception as e:
            logger.error(f"Failed to get companies hiring count: {e}")
            return 0

    # ========== Private Domain Methods (Anti-Corruption Layer) ==========

    def _fetch_dashboard_summary(self) -> DashboardSummary:
        """Fetch and normalize dashboard summary."""
        data = self.api_client.get("/api/v1/analytics/dashboard-summary")
        return self._normalize_response(data, DashboardSummary)

    def _fetch_top_skills(self, limit: int) -> list[TopSkill]:
        """Fetch and normalize top skills."""
        data = self.api_client.get("/api/v1/analytics/top-skills", params={"limit": limit})
        return self._normalize_list(data, TopSkill)

    def _fetch_top_companies(self, limit: int) -> list[TopCompany]:
        """Fetch and normalize top companies."""
        data = self.api_client.get("/api/v1/analytics/top-companies", params={"limit": limit})
        return self._normalize_list(data, TopCompany)

    def _fetch_jobs_by_location(self, limit: int) -> list[LocationAnalytics]:
        """Fetch and normalize jobs by location."""
        data = self.api_client.get("/api/v1/analytics/jobs-by-location", params={"limit": limit})
        return self._normalize_list(data, LocationAnalytics)

    def _fetch_salary_statistics(self) -> SalaryStatistics:
        """Fetch and normalize salary statistics."""
        data = self.api_client.get("/api/v1/analytics/salary-statistics")
        return self._normalize_response(data, SalaryStatistics)

    def _fetch_salary_distribution(self) -> list[SalaryDistribution]:
        """Fetch and normalize salary distribution."""
        data = self.api_client.get("/api/v1/analytics/salary-distribution")
        return self._normalize_list(data, SalaryDistribution)

    def _fetch_salary_by_location(self, limit: int) -> list:
        """Fetch and normalize salary by location."""
        data = self.api_client.get("/api/v1/analytics/salary-by-location", params={"limit": limit})
        from schemas.analytics import SalaryByLocation
        return self._normalize_list(data, SalaryByLocation)

    def _fetch_employment_types(self) -> list[EmploymentType]:
        """Fetch and normalize employment types."""
        data = self.api_client.get("/api/v1/analytics/employment-types")
        return self._normalize_list(data, EmploymentType)

    def _fetch_posting_trend(self, days: int) -> list[PostingTrend]:
        """Fetch and normalize posting trend."""
        data = self.api_client.get("/api/v1/analytics/posting-trend", params={"days": days})
        return self._normalize_list(data, PostingTrend)

    # ========== Helper Methods ==========

    def _normalize_response(self, data, model_class):
        """
        Normalize backend response to domain model.

        Handles None values gracefully for salary statistics.
        """
        try:
            if data is None:
                return model_class()

            if model_class.__name__ == "DashboardSummary":
                if "salary_statistics" not in data or data["salary_statistics"] is None:
                    data["salary_statistics"] = {
                        "average": 0,
                        "minimum": 0,
                        "maximum": 0,
                        "median": 0,
                        "sample_size": 0,
                        "currency": "USD",
                    }
                else:
                    stats = data["salary_statistics"]
                    for key in ["average", "minimum", "maximum", "median"]:
                        if stats.get(key) is None:
                            stats[key] = 0
                    if stats.get("currency") is None:
                        stats["currency"] = "USD"
                    if stats.get("sample_size") is None:
                        stats["sample_size"] = 0

            if model_class.__name__ == "SalaryStatistics":
                for key in ["average", "minimum", "maximum", "median"]:
                    if data.get(key) is None:
                        data[key] = 0
                if data.get("currency") is None:
                    data["currency"] = "USD"
                if data.get("sample_size") is None:
                    data["sample_size"] = 0

            return model_class(**data)
        except Exception as e:
            logger.error(f"Failed to normalize response to {model_class.__name__}: {e}")
            try:
                return model_class()
            except Exception:
                raise ValueError(f"Invalid response format for {model_class.__name__}")

    def _normalize_list(self, data, model_class):
        """Normalize list of backend responses."""
        return [self._normalize_response(item, model_class) for item in data]

    def refresh_all(self) -> None:
        """Clear all caches."""
        if self.cache_manager:
            self.cache_manager.clear()
            logger.info("Analytics cache cleared")