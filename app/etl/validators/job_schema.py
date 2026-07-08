# app/etl/validators/job_schema.py
"""Internal data contract for job listings using Pydantic validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class JobValidated(BaseModel):
    """
    Validated job record - the system's internal data contract.

    From this point onward, all downstream layers trust this structure.
    """

    # Pydantic v2 configuration
    model_config = ConfigDict(
        frozen=True,  # Immutable after creation
        str_strip_whitespace=True,  # Clean string fields
    )

    # Required fields - must be present and non-empty
    external_id: str = Field(min_length=1, description="Unique identifier from source")
    title: str = Field(min_length=1, description="Job title")

    # Optional fields - can be None
    company_name: str | None = Field(None, description="Company name")
    location: str | None = Field(None, description="Job location")
    description: str | None = Field(None, description="Job description")

    # Salary fields with validation
    salary_min: float | None = Field(default=None, ge=0, description="Minimum salary")
    salary_max: float | None = Field(default=None, ge=0, description="Maximum salary")
    currency: str | None = Field(None, min_length=3, max_length=3, description="Currency code")

    # Metadata - using Pydantic's HttpUrl for validation
    source: str = Field(default="adzuna", min_length=1, description="Data source")
    source_url: HttpUrl | None = Field(None, description="Original job URL")

    posted_date: datetime | None = Field(None, description="Job posting date")

    # ---- Validation logic ----

    @field_validator("posted_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        """Parse ISO format dates, handling Zulu timezone indicator."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Handle Z suffix (Zulu time) by converting to +00:00
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        raise ValueError(f"Invalid date format: {v}")

    @model_validator(mode="after")
    def validate_salary_range(self):
        """Ensure salary_min doesn't exceed salary_max."""
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError(
                f"salary_min ({self.salary_min}) cannot exceed salary_max ({self.salary_max})"
            )
        return self


def validate_job(job_dict: dict) -> JobValidated:
    """
    Convert transformed job dict to validated internal model.

    Args:
        job_dict: Transformed job dictionary from JobsTransformer

    Returns:
        JobValidated: Validated job record

    Raises:
        ValidationError: If data fails validation rules
    """
    return JobValidated(**job_dict)


def validate_jobs(jobs: list[dict]) -> list[JobValidated]:
    """
    Convert a list of transformed job dicts to validated models.

    Args:
        jobs: List of transformed job dictionaries

    Returns:
        List[JobValidated]: List of validated job records

    Raises:
        ValidationError: If any job fails validation
    """
    return [validate_job(job) for job in jobs]
