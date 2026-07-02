# app/schemas/job.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class JobResponse(BaseModel):
    """Response schema for a single job."""
    id: UUID
    title: str
    company_name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    posted_date: Optional[datetime] = None
    source_site: Optional[str] = None
    source_url: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class JobFilters(BaseModel):
    """Filter parameters for job listing."""
    company_name: Optional[str] = None
    location: Optional[str] = None
    source_site: Optional[str] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None


class JobListResponse(BaseModel):
    """Response schema for paginated job list."""
    page: int
    limit: int
    total: int
    data: List[JobResponse]