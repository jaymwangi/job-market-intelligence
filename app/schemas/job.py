"""Job API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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

    # Sprint 6.6: Enrichment fields
    skills: list[str] = Field(
        default_factory=list,
        description="Extracted technical skills",
    )
    technology_category: str | None = Field(
        default=None,
        description="Technology category (backend, frontend, data, devops, etc.)",
    )
    is_tech_role: bool = Field(
        default=True,
        description="Whether this is a technology role",
    )
    country_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="ISO 2-letter country code",
    )
    currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="ISO 3-letter currency code (normalized)",
    )
    employment_type: str | None = Field(
        default=None,
        description="Employment type (FULL_TIME, CONTRACT, etc.)",
    )

    class Config:
        from_attributes = True


class JobFilters(BaseModel):
    """Filter parameters for job listing."""

    company_name: str | None = None
    location: str | None = None
    source_site: str | None = None
    min_salary: float | None = None
    max_salary: float | None = None

    # Sprint 6.6: New enrichment filters
    country_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="Filter by ISO country code",
    )
    technology_category: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Filter by technology category (backend, frontend, data, etc.)",
    )
    employment_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Filter by employment type (FULL_TIME, CONTRACT, etc.)",
    )


class JobListResponse(BaseModel):
    """Response schema for paginated job list."""

    page: int
    limit: int
    total: int
    data: list[JobResponse]