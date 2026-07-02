# app/schemas/analytics.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TopSkillResponse(BaseModel):
    """Response schema for top skills."""
    skill: str
    count: int
    percentage: Optional[float] = None


class TopCompanyResponse(BaseModel):
    """Response schema for top companies."""
    company: str
    job_count: int
    percentage: Optional[float] = None


class LocationResponse(BaseModel):
    """Response schema for jobs by location."""
    location: str
    job_count: int
    percentage: Optional[float] = None


class SalaryStatisticsResponse(BaseModel):
    """Response schema for salary statistics."""
    average: Optional[float] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    median: Optional[float] = None
    sample_size: int = 0
    currency: Optional[str] = None


class EmploymentDistributionResponse(BaseModel):
    """Response schema for employment type distribution."""
    employment_type: str
    count: int
    percentage: Optional[float] = None


class SalaryDistributionResponse(BaseModel):
    """Response schema for salary distribution."""
    range: str
    count: int
    percentage: Optional[float] = None


class PostingTrendResponse(BaseModel):
    """Response schema for posting trends over time."""
    date: str
    count: int
    cumulative: Optional[int] = None


class DatasetSummaryResponse(BaseModel):
    """Response schema for dataset summary."""
    total_jobs: int
    unique_companies: int
    unique_locations: int
    unique_skills: int
    date_range: Dict[str, Optional[str]]
    last_updated: Optional[datetime] = None


class SalaryByLocationResponse(BaseModel):
    """Response schema for salary by location."""
    location: str
    average_salary: Optional[float] = None
    job_count: int
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None


class SalaryByCompanyResponse(BaseModel):
    """Response schema for salary by company."""
    company: str
    average_salary: Optional[float] = None
    job_count: int
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None


class OverviewResponse(BaseModel):
    """Lightweight overview response for general API consumers."""
    total_jobs: int = 0
    recent_jobs: int = 0
    top_company: Optional[str] = None
    top_skill: Optional[str] = None
    average_salary: Optional[float] = None


class DashboardSummaryResponse(BaseModel):
    """Dashboard-oriented response for Streamlit frontend."""
    total_jobs: int = 0
    recent_jobs_count: int = 0
    top_companies: List[TopCompanyResponse] = Field(default_factory=list)
    top_locations: List[LocationResponse] = Field(default_factory=list)
    top_skills: List[TopSkillResponse] = Field(default_factory=list)
    salary_statistics: SalaryStatisticsResponse = Field(default_factory=SalaryStatisticsResponse)
    employment_types: List[EmploymentDistributionResponse] = Field(default_factory=list)
    posting_trend: List[PostingTrendResponse] = Field(default_factory=list)