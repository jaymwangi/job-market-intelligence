# app/api/routes/jobs.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.session import get_db
from app.repositories.job_repository import JobRepository
from app.services.job_service import JobService
from app.schemas.job import JobFilters, JobListResponse, JobResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def get_service(db: Session = Depends(get_db)) -> JobService:
    """Dependency to get job service instance."""
    return JobService(JobRepository(db))


@router.get(
    "",
    response_model=JobListResponse,
    status_code=status.HTTP_200_OK,
    summary="List jobs",
    description="Get paginated list of jobs with optional search and filtering."
)
def get_jobs(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    q: str = Query(None, description="Search query for job titles or company names"),
    company_name: str = Query(None, description="Filter by company name"),
    location: str = Query(None, description="Filter by location"),
    source_site: str = Query(None, description="Filter by source site (e.g., 'adzuna')"),
    min_salary: float = Query(None, description="Minimum salary filter"),
    max_salary: float = Query(None, description="Maximum salary filter"),
    service: JobService = Depends(get_service)
):
    """
    Get paginated jobs with search and filters.
    
    Args:
        page: Page number
        limit: Items per page
        q: Search query
        company_name: Filter by company name
        location: Filter by location
        source_site: Filter by source site
        min_salary: Minimum salary
        max_salary: Maximum salary
        service: Job service instance
        
    Returns:
        Paginated job list
    """
    filters = JobFilters(
        company_name=company_name,
        location=location,
        source_site=source_site,
        min_salary=min_salary,
        max_salary=max_salary,
    )

    jobs, total = service.get_jobs(page, limit, filters, q)

    return JobListResponse(
        page=page,
        limit=limit,
        total=total,
        data=[JobResponse.model_validate(j) for j in jobs]
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job by ID",
    description="Get a single job by its ID."
)
def get_job(
    job_id: UUID,
    service: JobService = Depends(get_service)
):
    """
    Get a single job by ID.
    
    Args:
        job_id: Job ID
        service: Job service instance
        
    Returns:
        Job details
        
    Raises:
        HTTPException: 404 if job not found
    """
    job = service.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )

    return JobResponse.model_validate(job)