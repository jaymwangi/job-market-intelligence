# app/schemas/__init__.py
from .analytics import (
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
from .common import HealthResponse
from .job import JobFilters, JobListResponse, JobResponse

__all__ = [
    "HealthResponse",
    "JobResponse",
    "JobFilters",
    "JobListResponse",
    "TopSkillResponse",
    "TopCompanyResponse",
    "LocationResponse",
    "SalaryStatisticsResponse",
    "EmploymentDistributionResponse",
    "SalaryDistributionResponse",
    "PostingTrendResponse",
    "DatasetSummaryResponse",
    "SalaryByLocationResponse",
    "SalaryByCompanyResponse",
    "OverviewResponse",
    "DashboardSummaryResponse",
]
