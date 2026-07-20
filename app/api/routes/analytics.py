"""Analytics API routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
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
from app.services.analytics_service import AnalyticsService
from config import get_logger

logger = get_logger("app.api.routes.analytics")
router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency to get analytics service instance."""
    return AnalyticsService(AnalyticsRepository(db))


# ============================================================
# Existing Analytics Endpoints (unchanged)
# ============================================================


@router.get(
    "/top-skills",
    response_model=list[TopSkillResponse],
    status_code=status.HTTP_200_OK,
    summary="Get top skills",
    description="Get the most in-demand skills with job counts and percentages.",
)
def get_top_skills(
    limit: int = Query(10, ge=1, le=50, description="Number of skills to return"),
    service: AnalyticsService = Depends(get_service),
):
    """Get top skills by job count."""
    logger.debug("Fetching top %d skills", limit)
    return service.get_top_skills(limit)


@router.get(
    "/top-companies",
    response_model=list[TopCompanyResponse],
    status_code=status.HTTP_200_OK,
    summary="Get top companies",
    description="Get companies with the most job postings.",
)
def get_top_companies(
    limit: int = Query(10, ge=1, le=50, description="Number of companies to return"),
    service: AnalyticsService = Depends(get_service),
):
    """Get top companies by job count."""
    logger.debug("Fetching top %d companies", limit)
    return service.get_top_companies(limit)


@router.get(
    "/jobs-by-location",
    response_model=list[LocationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get jobs by location",
    description="Get job distribution by location.",
)
def get_jobs_by_location(
    limit: int = Query(10, ge=1, le=50, description="Number of locations to return"),
    service: AnalyticsService = Depends(get_service),
):
    """Get job distribution by location."""
    logger.debug("Fetching jobs by location (limit=%d)", limit)
    return service.get_jobs_by_location(limit)


@router.get(
    "/salary-statistics",
    response_model=SalaryStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get salary statistics",
    description="Get aggregate salary statistics (average, min, max, median).",
)
def get_salary_statistics(
    service: AnalyticsService = Depends(get_service),
):
    """Get salary statistics."""
    logger.debug("Fetching salary statistics")
    return service.get_salary_statistics()


@router.get(
    "/employment-types",
    response_model=list[EmploymentDistributionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get employment type distribution",
    description="Get distribution of employment types.",
)
def get_employment_types(
    service: AnalyticsService = Depends(get_service),
):
    """Get employment type distribution."""
    logger.debug("Fetching employment type distribution")
    return service.get_employment_types()


@router.get(
    "/salary-by-location",
    response_model=list[SalaryByLocationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get salary by location",
    description="Get average salary statistics grouped by location.",
)
def get_salary_by_location(
    limit: int = Query(10, ge=1, le=50, description="Number of locations to return"),
    service: AnalyticsService = Depends(get_service),
):
    """Get salary statistics by location."""
    logger.debug("Fetching salary by location (limit=%d)", limit)
    return service.get_salary_by_location(limit)


@router.get(
    "/salary-by-company",
    response_model=list[SalaryByCompanyResponse],
    status_code=status.HTTP_200_OK,
    summary="Get salary by company",
    description="Get average salary statistics grouped by company.",
)
def get_salary_by_company(
    limit: int = Query(10, ge=1, le=50, description="Number of companies to return"),
    service: AnalyticsService = Depends(get_service),
):
    """Get salary statistics by company."""
    logger.debug("Fetching salary by company (limit=%d)", limit)
    return service.get_salary_by_company(limit)


@router.get(
    "/posting-trend",
    response_model=list[PostingTrendResponse],
    status_code=status.HTTP_200_OK,
    summary="Get posting trends",
    description="Get job posting trends over time with cumulative counts.",
)
def get_posting_trend(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    service: AnalyticsService = Depends(get_service),
):
    """Get job posting trend over time."""
    logger.debug("Fetching posting trend for last %d days", days)
    return service.get_posting_trend(days)


@router.get(
    "/recent-jobs",
    response_model=int,
    status_code=status.HTTP_200_OK,
    summary="Get recent jobs count",
    description="Get count of jobs posted in the last N days.",
)
def get_recent_jobs(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    service: AnalyticsService = Depends(get_service),
):
    """Get count of recently posted jobs."""
    logger.debug("Fetching recent jobs count for last %d days", days)
    return service.get_recent_jobs_count(days)


@router.get(
    "/salary-distribution",
    response_model=list[SalaryDistributionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get salary distribution",
    description="Get salary distribution by salary ranges.",
)
def get_salary_distribution(
    service: AnalyticsService = Depends(get_service),
):
    """Get salary distribution."""
    logger.debug("Fetching salary distribution")
    return service.get_salary_distribution()


@router.get(
    "/dataset-summary",
    response_model=DatasetSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dataset summary",
    description="Get comprehensive dataset summary with statistics.",
)
def get_dataset_summary(
    service: AnalyticsService = Depends(get_service),
):
    """Get dataset summary."""
    logger.debug("Fetching dataset summary")
    return service.get_dataset_summary()


@router.get(
    "/overview",
    response_model=OverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get overview",
    description="Lightweight overview for general API consumers and monitoring.",
)
def get_overview(
    service: AnalyticsService = Depends(get_service),
):
    """Get lightweight overview."""
    logger.debug("Fetching overview")
    return service.get_overview()


@router.get(
    "/dashboard-summary",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dashboard summary",
    description="Complete dashboard summary for Streamlit frontend with all widgets.",
)
def get_dashboard_summary(
    service: AnalyticsService = Depends(get_service),
):
    """Get complete dashboard summary."""
    logger.debug("Fetching dashboard summary")
    return service.get_dashboard_summary()


# ============================================================
# Sprint 6.6: New Enrichment Analytics Endpoints (RESTful Resources)
# ============================================================


@router.get(
    "/enriched/skills",
    response_model=list[SkillCount],
    status_code=status.HTTP_200_OK,
    summary="Get enriched skills",
    description="Get skills with frequency counts and optional country filter.",
)
def get_enriched_skills(
    limit: int = Query(20, ge=1, le=100, description="Number of skills to return"),
    country_code: str | None = Query(
        None,
        min_length=2,
        max_length=2,
        description="Filter by country code (e.g., GB, US, DE)",
    ),
    service: AnalyticsService = Depends(get_service),
) -> list[SkillCount]:
    """
    Get skills with frequency counts and optional country filter.

    Args:
        limit: Number of skills to return (default: 20, max: 100)
        country_code: Optional country filter

    Returns:
        List of SkillCount objects with skill name and count
    """
    logger.debug(
        "Fetching enriched skills (limit=%d%s)",
        limit,
        f", country={country_code}" if country_code else "",
    )

    skills = service.get_enriched_top_skills(limit, country_code)

    logger.info("Retrieved %d enriched skills", len(skills))
    return skills


@router.get(
    "/enriched/countries",
    response_model=list[CountryDistribution],
    status_code=status.HTTP_200_OK,
    summary="Get country distribution",
    description="Get job distribution by country from enrichment data.",
)
def get_enriched_countries(
    service: AnalyticsService = Depends(get_service),
) -> list[CountryDistribution]:
    """
    Get job distribution by country.

    Returns:
        List of CountryDistribution objects with country and job count
    """
    logger.debug("Fetching country distribution")

    distribution = service.get_country_distribution()

    logger.info("Retrieved %d countries", len(distribution))
    return distribution


@router.get(
    "/enriched/technology",
    response_model=list[TechnologyDistribution],
    status_code=status.HTTP_200_OK,
    summary="Get technology distribution",
    description="Get distribution of technology categories from enrichment data.",
)
def get_enriched_technology(
    service: AnalyticsService = Depends(get_service),
) -> list[TechnologyDistribution]:
    """
    Get distribution of technology categories.

    Returns:
        List of TechnologyDistribution objects with category and job count
    """
    logger.debug("Fetching technology distribution")

    distribution = service.get_technology_distribution()

    logger.info("Retrieved %d technology categories", len(distribution))
    return distribution


@router.get(
    "/enriched/salary",
    response_model=SalaryStatistics,
    status_code=status.HTTP_200_OK,
    summary="Get enriched salary statistics",
    description="Get salary statistics with optional country filter from enrichment data.",
)
def get_enriched_salary(
    country_code: str | None = Query(
        None,
        min_length=2,
        max_length=2,
        description="Filter by country code",
    ),
    service: AnalyticsService = Depends(get_service),
) -> SalaryStatistics:
    """
    Get salary statistics with optional country filter.

    Args:
        country_code: Optional country filter

    Returns:
        SalaryStatistics object with salary metrics
    """
    logger.debug(
        "Fetching enriched salary statistics%s",
        f" for country {country_code}" if country_code else "",
    )

    stats = service.get_enriched_salary_statistics(country_code)

    logger.info("Retrieved enriched salary statistics")
    return stats