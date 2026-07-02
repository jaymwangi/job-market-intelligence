# app/api/routes/analytics.py
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database.session import get_db
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.analytics_service import AnalyticsService
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

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency to get analytics service instance."""
    return AnalyticsService(AnalyticsRepository(db))


@router.get(
    "/top-skills",
    response_model=list[TopSkillResponse],
    status_code=status.HTTP_200_OK,
    summary="Get top skills",
    description="Get the most in-demand skills with job counts and percentages."
)
def get_top_skills(
    limit: int = Query(10, ge=1, le=50, description="Number of skills to return"),
    service: AnalyticsService = Depends(get_service),
):
    """Get top skills by job count."""
    return service.get_top_skills(limit)


@router.get(
    "/top-companies",
    response_model=list[TopCompanyResponse],
    status_code=status.HTTP_200_OK,
    summary="Get top companies",
    description="Get companies with the most job postings."
)
def get_top_companies(
    limit: int = Query(10, ge=1, le=50, description="Number of companies to return"),
    service: AnalyticsService = Depends(get_service),
):
    """Get top companies by job count."""
    return service.get_top_companies(limit)


@router.get(
    "/jobs-by-location",
    response_model=list[LocationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get jobs by location",
    description="Get job distribution by location."
)
def get_jobs_by_location(
    limit: int = Query(10, ge=1, le=50, description="Number of locations to return"),
    service: AnalyticsService = Depends(get_service),
):
    """Get job distribution by location."""
    return service.get_jobs_by_location(limit)


@router.get(
    "/salary-statistics",
    response_model=SalaryStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get salary statistics",
    description="Get aggregate salary statistics (average, min, max, median)."
)
def get_salary_statistics(
    service: AnalyticsService = Depends(get_service),
):
    """Get salary statistics."""
    return service.get_salary_statistics()


@router.get(
    "/employment-types",
    response_model=list[EmploymentDistributionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get employment type distribution",
    description="Get distribution of employment types."
)
def get_employment_types(
    service: AnalyticsService = Depends(get_service),
):
    """Get employment type distribution."""
    return service.get_employment_types()


@router.get(
    "/salary-by-location",
    response_model=list[SalaryByLocationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get salary by location",
    description="Get average salary statistics grouped by location."
)
def get_salary_by_location(
    limit: int = Query(10, ge=1, le=50, description="Number of locations to return"),
    service: AnalyticsService = Depends(get_service),
):
    """Get salary statistics by location."""
    return service.get_salary_by_location(limit)


@router.get(
    "/salary-by-company",
    response_model=list[SalaryByCompanyResponse],
    status_code=status.HTTP_200_OK,
    summary="Get salary by company",
    description="Get average salary statistics grouped by company."
)
def get_salary_by_company(
    limit: int = Query(10, ge=1, le=50, description="Number of companies to return"),
    service: AnalyticsService = Depends(get_service),
):
    """Get salary statistics by company."""
    return service.get_salary_by_company(limit)


@router.get(
    "/posting-trend",
    response_model=list[PostingTrendResponse],
    status_code=status.HTTP_200_OK,
    summary="Get posting trends",
    description="Get job posting trends over time with cumulative counts."
)
def get_posting_trend(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    service: AnalyticsService = Depends(get_service),
):
    """Get job posting trend over time."""
    return service.get_posting_trend(days)


@router.get(
    "/recent-jobs",
    response_model=int,
    status_code=status.HTTP_200_OK,
    summary="Get recent jobs count",
    description="Get count of jobs posted in the last N days."
)
def get_recent_jobs(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    service: AnalyticsService = Depends(get_service),
):
    """Get count of recently posted jobs."""
    return service.get_recent_jobs_count(days)


@router.get(
    "/salary-distribution",
    response_model=list[SalaryDistributionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get salary distribution",
    description="Get salary distribution by salary ranges."
)
def get_salary_distribution(
    service: AnalyticsService = Depends(get_service),
):
    """Get salary distribution."""
    return service.get_salary_distribution()


@router.get(
    "/dataset-summary",
    response_model=DatasetSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dataset summary",
    description="Get comprehensive dataset summary with statistics."
)
def get_dataset_summary(
    service: AnalyticsService = Depends(get_service),
):
    """Get dataset summary."""
    return service.get_dataset_summary()


@router.get(
    "/overview",
    response_model=OverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get overview",
    description="Lightweight overview for general API consumers and monitoring."
)
def get_overview(
    service: AnalyticsService = Depends(get_service),
):
    """Get lightweight overview."""
    return service.get_overview()


@router.get(
    "/dashboard-summary",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dashboard summary",
    description="Complete dashboard summary for Streamlit frontend with all widgets."
)
def get_dashboard_summary(
    service: AnalyticsService = Depends(get_service),
):
    """Get complete dashboard summary."""
    return service.get_dashboard_summary()