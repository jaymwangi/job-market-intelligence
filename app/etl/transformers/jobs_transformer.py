"""Transform Adzuna API data to normalized internal format."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
from app.etl.schemas.transformed import JobTransformed
from app.etl.constants import RAW_SOURCE_COUNTRY_FIELD

logger = logging.getLogger(__name__)

# Type aliases
RawJob = Dict[str, Any]
RawJobs = List[RawJob]

# Employment type mapping
EMPLOYMENT_TYPES = {
    "full": "FULL_TIME",
    "part": "PART_TIME",
    "contract": "CONTRACT",
    "intern": "INTERNSHIP",
    "temporary": "TEMPORARY",
    "temp": "TEMPORARY",
    "permanent": "PERMANENT",
}


class JobsTransformer:
    """
    Transforms Adzuna job listings to a normalized internal format.

    The output is provider-agnostic, so the rest of the system
    doesn't need to know where the data came from.
    """

    SOURCE = "adzuna"

    def transform(self, raw_jobs: RawJobs) -> List[JobTransformed]:
        """
        Transform a list of raw job listings to JobTransformed objects.

        Args:
            raw_jobs: List of raw job dicts from Adzuna API

        Returns:
            List of JobTransformed objects
        """
        transformed = []

        for job in raw_jobs:
            transformed_job = self.transform_one(job)
            if transformed_job:
                transformed.append(transformed_job)

        logger.info(
            "Transformation complete: %d/%d jobs succeeded",
            len(transformed),
            len(raw_jobs),
        )
        return transformed

    def transform_one(self, job: RawJob) -> Optional[JobTransformed]:
        """
        Transform a single raw job listing to JobTransformed.

        Args:
            job: Raw job dict from Adzuna API

        Returns:
            JobTransformed object or None if transformation fails
        """
        try:
            # Extract source country from raw job metadata
            source_country = job.get(RAW_SOURCE_COUNTRY_FIELD)

            # Parse dates
            posted_date = self._parse_datetime(job.get("created"))
            scraped_date = posted_date or datetime.utcnow()

            # Extract category safely
            category = job.get("category", {})
            if isinstance(category, dict):
                category_label = category.get("label", "")
            else:
                category_label = str(category or "")

            return JobTransformed(
                source_id=str(job.get("id", "")),
                source=self.SOURCE,
                title=job.get("title", ""),
                company=self._company(job) or "Unknown",
                location=self._location(job) or "",
                description=job.get("description", ""),
                salary_min=self._salary(job, "min"),
                salary_max=self._salary(job, "max"),
                salary_currency=self._currency(job),
                employment_type=self._parse_employment_type(job),
                category=category_label,
                posted_date=posted_date,
                scraped_date=scraped_date,
                url=job.get("redirect_url", ""),
                source_country=source_country,
            )

        except Exception:
            logger.exception(
                "Failed transforming job %s",
                job.get("id", "unknown"),
            )
            return None

    def _company(self, job: RawJob) -> Optional[str]:
        """Extract company name from nested structure."""
        company = job.get("company")
        if isinstance(company, dict):
            return company.get("display_name")
        return company

    def _location(self, job: RawJob) -> Optional[str]:
        """Extract location from nested structure."""
        location = job.get("location")
        if isinstance(location, dict):
            return location.get("display_name")
        return location

    def _salary(self, job: RawJob, key: str) -> Optional[float]:
        """Extract salary min/max from nested structure."""
        # Try the 'salary' object first (Adzuna format)
        salary = job.get("salary")
        if isinstance(salary, dict):
            value = salary.get(key)
            if value is not None:
                parsed = self._to_float(value)
                if parsed is not None:
                    return parsed

        # Fall back to top-level fields
        fallback_key = f"salary_{key}"
        value = job.get(fallback_key)
        if value is not None:
            return self._to_float(value)

        return None

    def _currency(self, job: RawJob) -> Optional[str]:
        """Extract currency from nested structure."""
        # Try the 'salary' object first (Adzuna format)
        salary = job.get("salary")
        if isinstance(salary, dict):
            currency = salary.get("currency")
            if currency:
                return currency

        # Fall back to top-level field
        return job.get("salary_currency")

    def _parse_employment_type(self, job: RawJob) -> str:
        """Parse employment type using lookup table."""
        contract = job.get("contract_type", "")
        if not contract:
            contract = job.get("type", "")

        contract_lower = contract.lower()

        for keyword, employment_type in EMPLOYMENT_TYPES.items():
            if keyword in contract_lower:
                return employment_type

        return "OTHER"

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime using ISO-8601 format."""
        if not value:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            try:
                # Handle ISO-8601 with Z suffix
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None

        return None

    def _to_float(self, value: Any) -> Optional[float]:
        """Convert value to float, returning None if conversion fails."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.debug("Failed to convert value to float: %s", value)
            return None