# app/schemas/analytics.py
from datetime import datetime

from pydantic import BaseModel, Field


class TopSkillResponse(BaseModel):
    """Response schema for top skills."""

    skill: str
    count: int
    percentage: float | None = None


class TopCompanyResponse(BaseModel):
    """Response schema for top companies."""

    company: str
    job_count: int
    percentage: float | None = None


class LocationResponse(BaseModel):
    """Response schema for jobs by location."""

    location: str
    job_count: int
    percentage: float | None = None


class SalaryStatisticsResponse(BaseModel):
    """Response schema for salary statistics."""

    average: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    median: float | None = None
    sample_size: int = 0
    currency: str | None = None


class EmploymentDistributionResponse(BaseModel):
    """Response schema for employment type distribution."""

    employment_type: str
    count: int
    percentage: float | None = None


class SalaryDistributionResponse(BaseModel):
    """Response schema for salary distribution."""

    range: str
    count: int
    percentage: float | None = None


class PostingTrendResponse(BaseModel):
    """Response schema for posting trends over time."""

    date: str
    count: int
    cumulative: int | None = None


class DatasetSummaryResponse(BaseModel):
    """Response schema for dataset summary."""

    total_jobs: int
    unique_companies: int
    unique_locations: int
    unique_skills: int
    date_range: dict[str, str | None]
    last_updated: datetime | None = None


class SalaryByLocationResponse(BaseModel):
    """Response schema for salary by location."""

    location: str
    average_salary: float | None = None
    job_count: int
    min_salary: float | None = None
    max_salary: float | None = None


class SalaryByCompanyResponse(BaseModel):
    """Response schema for salary by company."""

    company: str
    average_salary: float | None = None
    job_count: int
    min_salary: float | None = None
    max_salary: float | None = None


class OverviewResponse(BaseModel):
    """Lightweight overview response for general API consumers."""

    total_jobs: int = 0
    recent_jobs: int = 0
    top_company: str | None = None
    top_skill: str | None = None
    average_salary: float | None = None


class DashboardSummaryResponse(BaseModel):
    """Dashboard-oriented response for Streamlit frontend."""

    total_jobs: int = 0
    recent_jobs_count: int = 0
    top_companies: list[TopCompanyResponse] = Field(default_factory=list)
    top_locations: list[LocationResponse] = Field(default_factory=list)
    top_skills: list[TopSkillResponse] = Field(default_factory=list)
    salary_statistics: SalaryStatisticsResponse = Field(default_factory=SalaryStatisticsResponse)
    employment_types: list[EmploymentDistributionResponse] = Field(default_factory=list)
    posting_trend: list[PostingTrendResponse] = Field(default_factory=list)
