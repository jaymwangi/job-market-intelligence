# app/etl/schemas/transformed.py

"""Transformed job schema - intermediate representation."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
    salary_min: float | None = Field(default=None, description="Minimum salary")
    salary_max: float | None = Field(default=None, description="Maximum salary")
    salary_currency: str | None = Field(default=None, description="Salary currency")

    # Other fields
    employment_type: str = Field(default="OTHER", description="Employment type")
    category: str = Field(default="", description="Job category")
    posted_date: datetime | None = Field(default=None, description="Date posted")
    scraped_date: datetime | None = Field(default=None, description="Date scraped")
    url: str = Field(default="", description="Job URL")

    # Extraction context
    source_country: str | None = Field(
        default=None,
        description="Country used for extraction (for normalization)",
    )

    # Acquisition metadata
    acquisition_tech_intent: bool | None = Field(
        default=None, description="Whether this job was acquired with tech intent"
    )
    acquisition_query: dict[str, Any] | None = Field(
        default=None, description="The query that acquired this job"
    )
    acquisition_country: str | None = Field(
        default=None, description="Country code for acquisition"
    )
    acquisition_mode: str | None = Field(default=None, description="Acquisition mode when acquired")
    acquisition_batch: int | None = Field(default=None, description="Batch number when acquired")

    model_config = ConfigDict(from_attributes=True)
