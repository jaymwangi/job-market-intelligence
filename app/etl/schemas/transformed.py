"""Transformed job schema - intermediate representation."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class JobTransformed(BaseModel):
    """Transformed job data - cleaned and mapped."""

    # Core fields
    source_id: str = Field(description="External source ID")
    source: str = Field(default="adzuna", description="Data source name")
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: str = Field(description="Location string")
    description: str = Field(default="", description="Job description")

    # Salary
    salary_min: Optional[float] = Field(default=None, description="Minimum salary")
    salary_max: Optional[float] = Field(default=None, description="Maximum salary")
    salary_currency: Optional[str] = Field(default=None, description="Salary currency")

    # Other fields
    employment_type: str = Field(default="OTHER", description="Employment type")
    category: str = Field(default="", description="Job category")
    posted_date: Optional[datetime] = Field(default=None, description="Date posted")
    scraped_date: Optional[datetime] = Field(default=None, description="Date scraped")
    url: str = Field(default="", description="Job URL")

    # Extraction context
    source_country: Optional[str] = Field(
        default=None,
        description="Country used for extraction (for normalization)",
    )

    class Config:
        from_attributes = True