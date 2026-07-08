# app/schemas/job.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobResponse(BaseModel):
    """Response schema for a single job."""

    id: UUID
    title: str
    company_name: str | None = None
    location: str | None = None
    description: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    posted_date: datetime | None = None
    source_site: str | None = None
    source_url: str | None = None
    is_active: bool = True

    class Config:
        from_attributes = True


class JobFilters(BaseModel):
    """Filter parameters for job listing."""

    company_name: str | None = None
    location: str | None = None
    source_site: str | None = None
    min_salary: float | None = None
    max_salary: float | None = None


class JobListResponse(BaseModel):
    """Response schema for paginated job list."""

    page: int
    limit: int
    total: int
    data: list[JobResponse]
