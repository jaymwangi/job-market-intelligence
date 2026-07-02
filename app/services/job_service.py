# app/services/job_service.py
"""Job service layer for business logic."""

from typing import Tuple, List, Optional
from uuid import UUID

from app.repositories.job_repository import JobRepository
from app.schemas.job import JobFilters
from app.models.job import Job


class JobService:
    """Service layer for job business logic."""

    def __init__(self, repo: JobRepository):
        self.repo = repo

    def get_jobs(
        self, 
        page: int, 
        limit: int, 
        filters: JobFilters, 
        search_query: Optional[str] = None
    ) -> Tuple[List[Job], int]:
        """
        Get paginated jobs with filters and search.
        
        Args:
            page: Page number (1-indexed)
            limit: Items per page (clamped to 1-100)
            filters: JobFilters object
            search_query: Optional search string
            
        Returns:
            Tuple of (jobs_list, total_count)
        """
        # Validate and sanitize pagination parameters
        page = max(page, 1)
        limit = min(max(limit, 1), 100)

        offset = (page - 1) * limit

        # Get jobs and total count
        jobs = self.repo.get_jobs(filters, offset, limit, search_query)
        total = self.repo.count_jobs(filters, search_query)

        return jobs, total

    def get_job(self, job_id: UUID) -> Optional[Job]:
        """
        Get a single job by ID.
        
        Args:
            job_id: Job ID to retrieve
            
        Returns:
            Job object or None if not found
        """
        return self.repo.get_by_id(job_id)