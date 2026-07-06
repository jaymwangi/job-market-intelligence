from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Job(BaseModel):
    """Frontend domain model for Job."""

    id: str
    title: str
    company_name: str
    location: str
    description: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = "USD"
    posted_date: datetime
    source_site: Optional[str] = None
    source_url: Optional[str] = None
    is_active: bool = True


class JobListResponse(BaseModel):
    """Frontend domain model - stable contract for UI."""

    items: List[Job]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobFilters(BaseModel):
    """
    Job filters - matches UI needs.

    Note: These will be translated to API parameters in the service layer.
    """

    search: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    source_site: Optional[str] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
