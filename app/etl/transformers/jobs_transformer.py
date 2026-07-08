# app/etl/transformers/jobs_transformer.py
"""Transform Adzuna API data to normalized internal format."""

from typing import Any


class JobsTransformer:
    """
    Transforms Adzuna job listings to a normalized internal format.

    The output is provider-agnostic, so the rest of the system
    doesn't need to know where the data came from.
    """

    SOURCE = "adzuna"

    def transform(self, raw_jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Transform a list of raw job listings.

        Args:
            raw_jobs: List of raw job dicts from Adzuna API

        Returns:
            List of normalized job dicts
        """
        return [self._transform_job(job) for job in raw_jobs]

    def transform_one(self, job: dict[str, Any]) -> dict[str, Any]:
        """
        Transform a single raw job listing.

        Args:
            job: Raw job dict from Adzuna API

        Returns:
            Normalized job dict
        """
        return self._transform_job(job)

    def _transform_job(self, job: dict[str, Any]) -> dict[str, Any]:
        """Internal method to transform a single job."""
        return {
            "external_id": self._safe(job, "id"),
            "title": self._safe(job, "title"),
            "company_name": self._company(job),
            "location": self._location(job),
            "description": self._safe(job, "description"),
            "salary_min": self._salary(job, "min"),
            "salary_max": self._salary(job, "max"),
            "currency": self._currency(job),
            "source": self.SOURCE,
            "source_url": self._safe(job, "redirect_url"),
            "posted_date": self._safe(job, "created"),
        }

    def _company(self, job: dict[str, Any]) -> str | None:
        """Extract company name from nested structure."""
        company = job.get("company")
        if isinstance(company, dict):
            return company.get("display_name")
        return company

    def _location(self, job: dict[str, Any]) -> str | None:
        """Extract location from nested structure."""
        location = job.get("location")
        if isinstance(location, dict):
            return location.get("display_name")
        return location

    def _salary(self, job: dict[str, Any], key: str) -> float | None:
        """Extract salary min/max from nested structure."""
        salary = job.get("salary")
        if isinstance(salary, dict):
            return salary.get(key)
        return None

    def _currency(self, job: dict[str, Any]) -> str | None:
        """Extract currency from nested structure."""
        salary = job.get("salary")
        if isinstance(salary, dict):
            return salary.get("currency")
        return job.get("salary_currency")

    def _safe(self, job: dict[str, Any], key: str) -> Any:
        """Safely get a value from a dict."""
        return job.get(key)
