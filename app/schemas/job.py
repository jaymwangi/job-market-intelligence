"""Job API schemas."""

from datetime import datetime
from uuid import UUID
from typing import TYPE_CHECKING
from decimal import Decimal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.models.job import Job


def _to_float(value: Decimal | float | None) -> float | None:
    """
    Convert Decimal to float, return None if value is None.
    
    Args:
        value: Decimal, float, or None
        
    Returns:
        float or None
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


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
    language: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="ISO 639-1 language code",
    )
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
        description="ISO 3166-1 alpha-2 country code",
    )
    currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code",
    )
    employment_type: str | None = Field(
        default=None,
        description="Employment type (FULL_TIME, CONTRACT, etc.)",
    )

    class Config:
        from_attributes = True

    @classmethod
    def from_model(cls, job: "Job") -> "JobResponse":
        """
        Create a JobResponse from a SQLAlchemy Job model.

        This converts ORM models to API responses, handling the conversion
        of Skill objects to skill names and Decimal to float.

        Args:
            job: SQLAlchemy Job model instance

        Returns:
            JobResponse with extracted and formatted data
        """
        # Extract skill names from Skill objects
        skill_names = [skill.name for skill in job.skills] if job.skills else []

        return cls(
            id=job.id,
            title=job.title,
            company_name=job.company_name,
            location=job.location,
            description=job.description,
            salary_min=_to_float(job.salary_min),
            salary_max=_to_float(job.salary_max),
            salary_currency=job.salary_currency,
            posted_date=job.posted_date,
            source_site=job.source_site,
            source_url=job.source_url,
            is_active=job.is_active,
            # Sprint 6.6: Enrichment fields
            language=job.language,
            skills=skill_names,
            technology_category=job.technology_category,
            is_tech_role=job.is_tech_role,
            country_code=job.country_code,
            currency=job.salary_currency,
            employment_type=job.employment_type,
        )


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
    # Sprint 6.6: Language filter
    language: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="Filter by ISO 639-1 language code (en, fr, de, etc.)",
    )
    # Sprint 6.6.1: Tech role filter
    is_tech_role: bool | None = Field(
        default=None,
        description="Filter to technology roles only",
    )


class JobListResponse(BaseModel):
    """Response schema for paginated job list."""

    page: int
    limit: int
    total: int
    total_pages: int
    data: list[JobResponse]