# app/services/analytics_service.py
"""Analytics service layer for business logic and orchestration."""

from typing import List, Dict, Optional, Any
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    TopSkillResponse,
    TopCompanyResponse,
    LocationResponse,
    SalaryStatisticsResponse,
    EmploymentDistributionResponse,
    SalaryDistributionResponse,
    PostingTrendResponse,
    DatasetSummaryResponse,
    SalaryByLocationResponse,
    SalaryByCompanyResponse,
    OverviewResponse,
    DashboardSummaryResponse,
)


class AnalyticsService:
    """Service layer for analytics orchestration."""

    def __init__(self, repo: AnalyticsRepository):
        self.repo = repo

    def get_top_skills(self, limit: int = 10) -> List[TopSkillResponse]:
        """Get top skills with counts and percentages."""
        results = self.repo.get_top_skills(limit)
        total = sum(r.get("count", 0) for r in results) if results else 1
        
        return [
            TopSkillResponse(
                skill=r.get("skill", ""),
                count=r.get("count", 0),
                percentage=(r.get("count", 0) / total * 100) if total > 0 else 0
            )
            for r in results
        ]

    def get_top_companies(self, limit: int = 10) -> List[TopCompanyResponse]:
        """Get top companies with job counts and percentages."""
        results = self.repo.get_top_companies(limit)
        total = sum(r.get("job_count", 0) for r in results) if results else 1
        
        return [
            TopCompanyResponse(
                company=r.get("company", ""),
                job_count=r.get("job_count", 0),
                percentage=(r.get("job_count", 0) / total * 100) if total > 0 else 0
            )
            for r in results
        ]

    def get_jobs_by_location(self, limit: int = 10) -> List[LocationResponse]:
        """Get job distribution by location with percentages."""
        results = self.repo.get_jobs_by_location(limit)
        total = sum(r.get("job_count", 0) for r in results) if results else 1
        
        return [
            LocationResponse(
                location=r.get("location", "Unknown"),
                job_count=r.get("job_count", 0),
                percentage=(r.get("job_count", 0) / total * 100) if total > 0 else 0
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

    def get_employment_types(self) -> List[EmploymentDistributionResponse]:
        """Get employment type distribution with percentages."""
        results = self.repo.get_employment_type_distribution()
        total = sum(r.get("count", 0) for r in results) if results else 1
        
        return [
            EmploymentDistributionResponse(
                employment_type=r.get("employment_type", "Unknown"),
                count=r.get("count", 0),
                percentage=(r.get("count", 0) / total * 100) if total > 0 else 0
            )
            for r in results
        ]

    def get_salary_by_location(self, limit: int = 10) -> List[SalaryByLocationResponse]:
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

    def get_salary_by_company(self, limit: int = 10) -> List[SalaryByCompanyResponse]:
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

    def get_posting_trend(self, days: int = 30) -> List[PostingTrendResponse]:
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

    def get_salary_distribution(self) -> List[SalaryDistributionResponse]:
        """Get salary distribution by ranges with percentages."""
        results = self.repo.get_salary_distribution()
        total = sum(r.get("count", 0) for r in results) if results else 1
        
        return [
            SalaryDistributionResponse(
                range=r.get("range", ""),
                count=r.get("count", 0),
                percentage=(r.get("count", 0) / total * 100) if total > 0 else 0
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
        return DashboardSummaryResponse(
            total_jobs=self.repo.get_total_jobs(),
            recent_jobs_count=self.repo.count_recent_jobs(7),
            top_companies=self.get_top_companies(10),
            top_locations=self.get_jobs_by_location(10),
            top_skills=self.get_top_skills(10),
            salary_statistics=self.get_salary_statistics(),
            employment_types=self.get_employment_types(),
            posting_trend=self.get_posting_trend(30),
        )