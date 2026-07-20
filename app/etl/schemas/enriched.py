"""Enriched job schema - adds intelligence data."""

from typing import Optional, List
from pydantic import Field
from app.etl.schemas.transformed import JobTransformed


class JobEnriched(JobTransformed):
    """Enriched job schema with intelligence data."""

    # Added by enrichment layer
    skills: List[str] = Field(default_factory=list, description="Extracted skills")
    technology_category: Optional[str] = Field(default=None, description="Technology category")
    is_tech_role: bool = Field(default=True, description="Whether this is a tech role")
    country_code: Optional[str] = Field(default=None, description="ISO country code")
    currency: Optional[str] = Field(default=None, description="ISO currency code")

    # Optional salary normalization
    normalized_salary_min: Optional[float] = Field(default=None, description="Normalized min salary")
    normalized_salary_max: Optional[float] = Field(default=None, description="Normalized max salary")