# app/schemas/__init__.py
from .common import HealthResponse
from .job import JobResponse, JobFilters, JobListResponse
from .analytics import (
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