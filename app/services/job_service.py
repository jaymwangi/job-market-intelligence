"""Job service layer for business logic."""

from uuid import UUID
from typing import List, Dict, Any, Optional

from fastapi import HTTPException, status

from app.models.job import Job
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobFilters
import logging

logger = logging.getLogger(__name__)


class JobService:
    """Service layer for job business logic."""

    def __init__(self, repo: JobRepository):
        self.repo = repo

    def get_jobs(
        self, page: int, limit: int, filters: JobFilters, search_query: str | None = None
    ) -> tuple[list[Job], int]:
        """
        Get paginated jobs with filters and search.

        Args:
            page: Page number (1-indexed)
            limit: Items per page (clamped to 1-100)
            filters: JobFilters object
            search_query: Optional search string

        Returns:
            Tuple of (jobs_list, total_count)

        Raises:
            HTTPException: If pagination parameters are invalid
        """
        # Validate and sanitize pagination parameters
        if page < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="page must be >= 1")

        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="limit must be between 1 and 100"
            )

        offset = (page - 1) * limit

        # Get jobs and total count
        try:
            jobs = self.repo.get_jobs(filters, offset, limit, search_query)
            total = self.repo.count_jobs(filters, search_query)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve jobs"
            )

        return jobs, total

    def get_job(self, job_id: UUID) -> Job | None:
        """
        Get a single job by ID.

        Args:
            job_id: Job UUID to retrieve

        Returns:
            Job object or None if not found
        """
        try:
            return self.repo.get_by_id(job_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve job"
            )

    # ============================================================
    # Sprint 6.6: Analytics Methods
    # ============================================================

    def get_top_skills(
        self,
        limit: int = 20,
        country_code: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get the most frequently occurring skills.

        Args:
            limit: Number of skills to return (default: 20)
            country_code: Optional country filter

        Returns:
            List of dicts with skill name and count
        """
        logger.debug(
            "Fetching top %d skills%s",
            limit,
            f" for country {country_code}" if country_code else "",
        )

        try:
            return self.repo.get_top_skills(limit, country_code)
        except Exception:
            logger.exception("Failed to fetch top skills")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve top skills",
            )

    def get_country_distribution(self) -> List[Dict[str, Any]]:
        """
        Get job distribution by country.

        Returns:
            List of dicts with country and job count
        """
        logger.debug("Fetching country distribution")

        try:
            return self.repo.get_country_distribution()
        except Exception:
            logger.exception("Failed to fetch country distribution")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve country distribution",
            )

    def get_technology_distribution(self) -> List[Dict[str, Any]]:
        """
        Get distribution of technology categories.

        Returns:
            List of dicts with category and job count
        """
        logger.debug("Fetching technology distribution")

        try:
            return self.repo.get_technology_distribution()
        except Exception:
            logger.exception("Failed to fetch technology distribution")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve technology distribution",
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics about jobs.

        Returns:
            Dict with various statistics including:
            - total_jobs: Total number of jobs
            - total_companies: Number of unique companies
            - total_countries: Number of unique countries
            - total_skills: Number of unique skills
            - average_salary_min: Average minimum salary
            - average_salary_max: Average maximum salary
            - tech_roles: Number of technology roles
        """
        logger.debug("Fetching job statistics")

        try:
            return self.repo.get_stats()
        except Exception:
            logger.exception("Failed to fetch job statistics")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve job statistics",
            )