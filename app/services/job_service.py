# app/services/job_service.py
"""Job service layer for business logic."""

from typing import Tuple, List, Optional
from uuid import UUID
from fastapi import HTTPException, status

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
            
        Raises:
            HTTPException: If pagination parameters are invalid
        """
        # Validate and sanitize pagination parameters
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page must be >= 1"
            )
        
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="limit must be between 1 and 100"
            )

        offset = (page - 1) * limit

        # Get jobs and total count
        try:
            jobs = self.repo.get_jobs(filters, offset, limit, search_query)
            total = self.repo.count_jobs(filters, search_query)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve jobs"
            )

        return jobs, total

    def get_job(self, job_id: UUID) -> Optional[Job]:
        """
        Get a single job by ID.
        
        Args:
            job_id: Job UUID to retrieve
            
        Returns:
            Job object or None if not found
        """
        try:
            return self.repo.get_by_id(job_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve job"
            )