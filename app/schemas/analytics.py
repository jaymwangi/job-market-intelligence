from datetime import datetime

from pydantic import BaseModel, Field


# ============================================================
# Existing Schemas (unchanged)
# ============================================================


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
    """
    Dashboard-oriented response for Streamlit frontend.
    
    Contains all metrics needed for the main dashboard view.
    """

    total_jobs: int = 0
    recent_jobs_count: int = 0

    # New: Summary metrics for dataset overview
    unique_companies: int = 0
    unique_locations: int = 0
    unique_skills: int = 0

    # Top lists
    top_companies: list[TopCompanyResponse] = Field(default_factory=list)
    top_locations: list[LocationResponse] = Field(default_factory=list)
    top_skills: list[TopSkillResponse] = Field(default_factory=list)

    # Salary statistics
    salary_statistics: SalaryStatisticsResponse = Field(default_factory=SalaryStatisticsResponse)

    # Employment distribution
    employment_types: list[EmploymentDistributionResponse] = Field(default_factory=list)

    # Time series
    posting_trend: list[PostingTrendResponse] = Field(default_factory=list)


# ============================================================
# Sprint 6.6: New Enrichment Schemas (RESTful Resources)
# ============================================================


class SkillCount(BaseModel):
    """Response schema for skill with frequency count."""

    skill: str = Field(description="Skill name")
    count: int = Field(description="Number of jobs mentioning this skill")


class CountryDistribution(BaseModel):
    """Response schema for country with job count."""

    country: str = Field(description="Country name or code")
    count: int = Field(description="Number of jobs in this country")


class TechnologyDistribution(BaseModel):
    """Response schema for technology category with job count."""

    category: str = Field(description="Technology category name (backend, frontend, data, etc.)")
    count: int = Field(description="Number of jobs in this category")


class SalaryStatistics(BaseModel):
    """Response schema for enriched salary statistics."""

    average_min: float | None = Field(None, description="Average minimum salary")
    average_max: float | None = Field(None, description="Average maximum salary")
    minimum: float | None = Field(None, description="Minimum salary")
    maximum: float | None = Field(None, description="Maximum salary")
    median: float | None = Field(None, description="Median salary")
    currency: str = Field("USD", description="Currency code")