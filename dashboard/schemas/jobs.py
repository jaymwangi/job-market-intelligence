from datetime import datetime

from pydantic import BaseModel


class Job(BaseModel):
    """Frontend domain model for Job."""

    id: str
    title: str
    company_name: str
    location: str
    description: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = "USD"
    posted_date: datetime
    source_site: str | None = None
    source_url: str | None = None
    is_active: bool = True


class JobListResponse(BaseModel):
    """Frontend domain model - stable contract for UI."""

    items: list[Job]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobFilters(BaseModel):
    """
    Job filters - matches UI needs.

    Note: These will be translated to API parameters in the service layer.
    """

    search: str | None = None
    company: str | None = None
    location: str | None = None
    source_site: str | None = None
    min_salary: float | None = None
    max_salary: float | None = None
