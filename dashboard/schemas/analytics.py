"""Domain models for analytics data."""

from datetime import datetime

from pydantic import BaseModel


class TopSkill(BaseModel):
    """Domain model for top skills."""

    skill: str
    count: int
    percentage: float


class TopCompany(BaseModel):
    """Domain model for top companies."""

    company: str
    job_count: int
    percentage: float


class LocationAnalytics(BaseModel):
    """Domain model for location analytics."""

    location: str
    job_count: int
    percentage: float


class SalaryStatistics(BaseModel):
    """Domain model for salary statistics."""

    average: float
    minimum: float
    maximum: float
    median: float
    sample_size: int
    currency: str = "USD"


class SalaryByLocation(BaseModel):
    """Domain model for salary by location."""

    location: str
    average_salary: float
    job_count: int
    min_salary: float
    max_salary: float


class SalaryByCompany(BaseModel):
    """Domain model for salary by company."""

    company: str
    average_salary: float
    job_count: int
    min_salary: float
    max_salary: float


class SalaryDistribution(BaseModel):
    """Domain model for salary distribution."""

    range: str
    count: int
    percentage: float


class EmploymentType(BaseModel):
    """Domain model for employment types."""

    employment_type: str
    count: int
    percentage: float


class PostingTrend(BaseModel):
    """Domain model for posting trends."""

    date: str
    count: int
    cumulative: int


class DatasetSummary(BaseModel):
    """Domain model for dataset summary."""

    total_jobs: int
    unique_companies: int
    unique_locations: int
    unique_skills: int
    date_range: dict
    last_updated: datetime


class DashboardSummary(BaseModel):
    """Domain model for complete dashboard summary."""

    total_jobs: int
    recent_jobs_count: int

    # New: Summary metrics for dataset overview
    unique_companies: int = 0
    unique_locations: int = 0
    unique_skills: int = 0

    top_companies: list[TopCompany]
    top_locations: list[LocationAnalytics]
    top_skills: list[TopSkill]
    salary_statistics: SalaryStatistics
    employment_types: list[EmploymentType]
    posting_trend: list[PostingTrend]