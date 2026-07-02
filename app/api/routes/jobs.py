# app/api/routes/jobs.py
from fastapi import APIRouter, Depends, Query, HTTPException, status, Path
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from config import get_logger
from app.database.session import get_db
from app.repositories.job_repository import JobRepository
from app.services.job_service import JobService
from app.schemas.job import JobFilters, JobListResponse, JobResponse

# Get logger for this module
logger = get_logger("app.api.routes.jobs")
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
    page: int = Query(
        1,
        ge=1,
        description="Page number (starts at 1)"
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Items per page (max 100)"
    ),
    q: Optional[str] = Query(
        None,
        min_length=1,
        max_length=200,
        description="Search query for job titles or company names"
    ),
    company_name: Optional[str] = Query(
        None,
        min_length=1,
        max_length=200,
        description="Filter by company name"
    ),
    location: Optional[str] = Query(
        None,
        min_length=1,
        max_length=200,
        description="Filter by location"
    ),
    source_site: Optional[str] = Query(
        None,
        min_length=1,
        max_length=50,
        description="Filter by source site (e.g., 'adzuna')"
    ),
    min_salary: Optional[float] = Query(
        None,
        ge=0,
        description="Minimum salary filter"
    ),
    max_salary: Optional[float] = Query(
        None,
        ge=0,
        description="Maximum salary filter"
    ),
    service: JobService = Depends(get_service)
):
    """
    Get paginated jobs with search and filters.
    """
    # Log the request (debug level - only shown in debug mode)
    logger.debug(f"Fetching jobs: page={page}, limit={limit}, q={q}")
    
    # Validate salary range
    if min_salary is not None and max_salary is not None:
        if min_salary > max_salary:
            logger.warning(f"Invalid salary range: min={min_salary}, max={max_salary}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="min_salary cannot be greater than max_salary"
            )
    
    filters = JobFilters(
        company_name=company_name,
        location=location,
        source_site=source_site,
        min_salary=min_salary,
        max_salary=max_salary,
    )

    jobs, total = service.get_jobs(page, limit, filters, q)

    # Log result (info level - shown in production)
    logger.info(f"Retrieved {len(jobs)} jobs (total: {total})")
    
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
    description="Get a single job by its UUID."
)
def get_job(
    job_id: UUID = Path(..., description="Job UUID"),
    service: JobService = Depends(get_service)
):
    """
    Get a single job by ID.
    """
    logger.debug(f"Fetching job: {job_id}")
    
    job = service.get_job(job_id)

    if not job:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )

    logger.info(f"Retrieved job: {job_id}")
    return JobResponse.model_validate(job)