"""Legacy validation models for backward compatibility."""
from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class JobValidatedModel(BaseModel):
    """
    Validated job record - the system's internal data contract.

    From this point onward, all downstream layers trust this structure.
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    # Required fields
    external_id: str = Field(min_length=1, description="Unique identifier from source")
    title: str = Field(min_length=1, description="Job title")

    # Optional fields
    company_name: str | None = Field(None, description="Company name")
    location: str | None = Field(None, description="Job location")
    description: str | None = Field(None, description="Job description")

    # Salary fields
    salary_min: float | None = Field(default=None, ge=0, description="Minimum salary")
    salary_max: float | None = Field(default=None, ge=0, description="Maximum salary")
    currency: str | None = Field(None, min_length=3, max_length=3, description="Currency code")

    # Metadata
    source: str = Field(default="adzuna", min_length=1, description="Data source")
    source_url: HttpUrl | None = Field(None, description="Original job URL")
    posted_date: datetime | None = Field(None, description="Job posting date")

    @field_validator("posted_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        """Parse ISO format dates, handling Zulu timezone indicator."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
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


def validate_job(job_dict: Dict[str, Any]) -> JobValidatedModel:
    """
    Convert transformed job dict to validated internal model.

    Args:
        job_dict: Transformed job dictionary from JobsTransformer

    Returns:
        JobValidatedModel: Validated job record

    Raises:
        ValidationError: If data fails validation rules
    """
    return JobValidatedModel(**job_dict)


def validate_jobs(jobs: List[Dict[str, Any]]) -> List[JobValidatedModel]:
    """
    Convert a list of transformed job dicts to validated models.

    Args:
        jobs: List of transformed job dictionaries

    Returns:
        List[JobValidatedModel]: List of validated job records

    Raises:
        ValidationError: If any job fails validation
    """
    return [validate_job(job) for job in jobs]