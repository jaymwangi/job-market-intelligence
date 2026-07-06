# dashboard/services/analytics_service.py
"""Analytics service with full transformation pipeline."""

import logging
from typing import List, Optional

from dashboard.api.client import APIClient
from dashboard.mappers.analytics_mapper import AnalyticsMapper
from dashboard.schemas.analytics import (
    DashboardSummary,
    EmploymentType,
    LocationAnalytics,
    PostingTrend,
    SalaryDistribution,
    SalaryStatistics,
    TopCompany,
    TopSkill,
)
from dashboard.schemas.chart_data import (
    BarChartData,
    DonutChartData,
    HistogramData,
    HorizontalBarChartData,
    LineChartData,
    MetricCardData,
    PieChartData,
)
from dashboard.services.base import BaseService
from dashboard.utils.cache import CacheManager, cached

logger = logging.getLogger(__name__)


class AnalyticsService(BaseService):
    """
    Analytics service with full transformation pipeline.

    The service owns the entire transformation chain:
    1. Fetch data from API
    2. Validate and normalize to domain models
    3. Transform to chart models via mapper
    4. Return presentation-ready data
    """

    def __init__(
        self, api_client: APIClient, cache_manager: Optional[CacheManager] = None
    ):
        super().__init__(api_client, cache_manager)
        self.mapper = AnalyticsMapper()

    # ========== Chart Model Methods (Presentation-Ready) ==========

    @cached(ttl=300)
    def get_dashboard_metrics(self) -> List[MetricCardData]:
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
            return HorizontalBarChartData(
                title="Most In-Demand Skills", x_values=[], y_values=[]
            )

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
    def get_salary_statistics(self) -> Optional[SalaryStatistics]:
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
            return BarChartData(
                title="Average Salary by Location", x_values=[], y_values=[]
            )

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
            return DonutChartData(
                title="Employment Type Distribution", labels=[], values=[]
            )

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
            return BarChartData(
                title="Employment Type Counts", x_values=[], y_values=[]
            )

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
            return LineChartData(
                title="Job Postings Over Time", x_values=[], y_values=[]
            )

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

    # ========== Private Domain Methods (Anti-Corruption Layer) ==========

    def _fetch_dashboard_summary(self) -> DashboardSummary:
        """Fetch and normalize dashboard summary."""
        data = self.api_client.get("/api/v1/analytics/dashboard-summary")
        return self._normalize_response(data, DashboardSummary)

    def _fetch_top_skills(self, limit: int) -> List[TopSkill]:
        """Fetch and normalize top skills."""
        data = self.api_client.get(
            "/api/v1/analytics/top-skills", params={"limit": limit}
        )
        return self._normalize_list(data, TopSkill)

    def _fetch_top_companies(self, limit: int) -> List[TopCompany]:
        """Fetch and normalize top companies."""
        data = self.api_client.get(
            "/api/v1/analytics/top-companies", params={"limit": limit}
        )
        return self._normalize_list(data, TopCompany)

    def _fetch_jobs_by_location(self, limit: int) -> List[LocationAnalytics]:
        """Fetch and normalize jobs by location."""
        data = self.api_client.get(
            "/api/v1/analytics/jobs-by-location", params={"limit": limit}
        )
        return self._normalize_list(data, LocationAnalytics)

    def _fetch_salary_statistics(self) -> SalaryStatistics:
        """Fetch and normalize salary statistics."""
        data = self.api_client.get("/api/v1/analytics/salary-statistics")
        return self._normalize_response(data, SalaryStatistics)

    def _fetch_salary_distribution(self) -> List[SalaryDistribution]:
        """Fetch and normalize salary distribution."""
        data = self.api_client.get("/api/v1/analytics/salary-distribution")
        return self._normalize_list(data, SalaryDistribution)

    def _fetch_salary_by_location(self, limit: int) -> List:
        """Fetch and normalize salary by location."""
        data = self.api_client.get(
            "/api/v1/analytics/salary-by-location", params={"limit": limit}
        )
        # Import here to avoid circular imports
        from dashboard.schemas.analytics import SalaryByLocation

        return self._normalize_list(data, SalaryByLocation)

    def _fetch_employment_types(self) -> List[EmploymentType]:
        """Fetch and normalize employment types."""
        data = self.api_client.get("/api/v1/analytics/employment-types")
        return self._normalize_list(data, EmploymentType)

    def _fetch_posting_trend(self, days: int) -> List[PostingTrend]:
        """Fetch and normalize posting trend."""
        data = self.api_client.get(
            "/api/v1/analytics/posting-trend", params={"days": days}
        )
        return self._normalize_list(data, PostingTrend)

    # ========== Helper Methods ==========

    def _normalize_response(self, data, model_class):
        """
        Normalize backend response to domain model.
        
        Handles None values gracefully for salary statistics.
        """
        try:
            # If data is None, return a default instance
            if data is None:
                return model_class()
            
            # Special handling for DashboardSummary
            if model_class.__name__ == "DashboardSummary":
                # Ensure salary_statistics exists
                if "salary_statistics" not in data or data["salary_statistics"] is None:
                    data["salary_statistics"] = {
                        "average": 0,
                        "minimum": 0,
                        "maximum": 0,
                        "median": 0,
                        "sample_size": 0,
                        "currency": "USD"
                    }
                else:
                    # Clean up salary_statistics fields
                    stats = data["salary_statistics"]
                    for key in ["average", "minimum", "maximum", "median"]:
                        if stats.get(key) is None:
                            stats[key] = 0
                    if stats.get("currency") is None:
                        stats["currency"] = "USD"
                    if stats.get("sample_size") is None:
                        stats["sample_size"] = 0
            
            # Special handling for SalaryStatistics
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
            # Return a default instance instead of raising
            try:
                return model_class()
            except:
                raise ValueError(f"Invalid response format for {model_class.__name__}")

    def _normalize_list(self, data, model_class):
        """Normalize list of backend responses."""
        return [self._normalize_response(item, model_class) for item in data]

    def refresh_all(self) -> None:
        """Clear all caches."""
        if self.cache_manager:
            self.cache_manager.clear()
            logger.info("Analytics cache cleared")