"""Jobs API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobFilters, JobListResponse, JobResponse
from app.services.job_service import JobService
from app.services.translation.service import get_translation_service
from config import get_logger

# Get logger for this module
logger = get_logger("app.api.routes.jobs")
router = APIRouter(prefix="/jobs", tags=["Jobs"])


def get_service(db: Session = Depends(get_db)) -> JobService:
    """Dependency to get job service instance."""
    return JobService(JobRepository(db))


# ============================================================
# Static routes first (no path parameters)
# ============================================================


@router.get(
    "",
    response_model=JobListResponse,
    status_code=status.HTTP_200_OK,
    summary="List jobs",
    description="Get paginated list of jobs with optional search and filtering.",
)
def get_jobs(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    q: str | None = Query(
        None,
        min_length=1,
        max_length=200,
        description="Search query for job titles or company names",
    ),
    company_name: str | None = Query(
        None, min_length=1, max_length=200, description="Filter by company name"
    ),
    location: str | None = Query(
        None, min_length=1, max_length=200, description="Filter by location"
    ),
    source_site: str | None = Query(
        None, min_length=1, max_length=50, description="Filter by source site (e.g., 'adzuna')"
    ),
    min_salary: float | None = Query(None, ge=0, description="Minimum salary filter"),
    max_salary: float | None = Query(None, ge=0, description="Maximum salary filter"),
    # Sprint 6.6: New enrichment filters
    country_code: str | None = Query(
        None,
        min_length=2,
        max_length=2,
        description="Filter by ISO country code (e.g., GB, US, DE)",
    ),
    technology_category: str | None = Query(
        None,
        min_length=1,
        max_length=50,
        description="Filter by technology category (e.g., backend, frontend, data)",
    ),
    employment_type: str | None = Query(
        None,
        min_length=1,
        max_length=50,
        description="Filter by employment type (e.g., FULL_TIME, CONTRACT)",
    ),
    # Sprint 6.6.1: Tech role filter
    is_tech_role: bool | None = Query(
        None,
        description="Filter to technology roles only",
    ),
    # Sprint 6.6: Language filter
    language: str | None = Query(
        None,
        min_length=2,
        max_length=2,
        description="Filter by ISO language code (e.g., en, fr, de)",
    ),
    service: JobService = Depends(get_service),
):
    """
    Get paginated jobs with search and filters.

    Supports filtering by:
    - Company name
    - Location
    - Source site
    - Salary range
    - Country code (Sprint 6.6)
    - Technology category (Sprint 6.6)
    - Employment type (Sprint 6.6)
    - Technology role (Sprint 6.6.1)
    - Language (Sprint 6.6)
    """
    # Log the request (debug level - only shown in debug mode)
    logger.debug(f"Fetching jobs: page={page}, limit={limit}, q={q}")

    # Validate salary range
    if min_salary is not None and max_salary is not None:
        if min_salary > max_salary:
            logger.warning(f"Invalid salary range: min={min_salary}, max={max_salary}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="min_salary cannot be greater than max_salary",
            )

    filters = JobFilters(
        company_name=company_name,
        location=location,
        source_site=source_site,
        min_salary=min_salary,
        max_salary=max_salary,
        country_code=country_code,
        technology_category=technology_category,
        employment_type=employment_type,
        is_tech_role=is_tech_role,
        language=language,
    )

    jobs, total = service.get_jobs(page, limit, filters, q)

    # Calculate total pages
    total_pages = (total + limit - 1) // limit if total > 0 else 0

    # Log result (info level - shown in production)
    logger.info(f"Retrieved {len(jobs)} jobs (total: {total})")

    return JobListResponse(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        data=[JobResponse.from_model(job) for job in jobs],
    )


@router.get(
    "/skills/top",
    response_model=list[dict[str, str | int]],
    status_code=status.HTTP_200_OK,
    summary="Get top skills",
    description="Get the most frequently occurring skills across all jobs.",
)
def get_top_skills(
    limit: int = Query(20, ge=1, le=100, description="Number of skills to return"),
    country_code: str | None = Query(
        None,
        min_length=2,
        max_length=2,
        description="Filter by country code",
    ),
    service: JobService = Depends(get_service),
) -> list[dict[str, str | int]]:
    """
    Get the most frequently occurring skills.
    """
    logger.debug(f"Fetching top {limit} skills" + (f" for country {country_code}" if country_code else ""))

    skills = service.get_top_skills(limit, country_code)

    logger.info(f"Retrieved {len(skills)} top skills")
    return skills


@router.get(
    "/countries/distribution",
    response_model=list[dict[str, str | int]],
    status_code=status.HTTP_200_OK,
    summary="Get job distribution by country",
    description="Get the number of jobs per country.",
)
def get_country_distribution(
    service: JobService = Depends(get_service),
) -> list[dict[str, str | int]]:
    """
    Get the number of jobs per country.
    """
    logger.debug("Fetching country distribution")

    distribution = service.get_country_distribution()

    logger.info(f"Retrieved {len(distribution)} countries")
    return distribution


@router.get(
    "/technology/distribution",
    response_model=list[dict[str, str | int]],
    status_code=status.HTTP_200_OK,
    summary="Get technology category distribution",
    description="Get the distribution of technology categories.",
)
def get_technology_distribution(
    service: JobService = Depends(get_service),
) -> list[dict[str, str | int]]:
    """
    Get the distribution of technology categories.
    """
    logger.debug("Fetching technology distribution")

    distribution = service.get_technology_distribution()

    logger.info(f"Retrieved {len(distribution)} technology categories")
    return distribution


@router.get(
    "/stats/summary",
    response_model=dict[str, int | float | None],
    status_code=status.HTTP_200_OK,
    summary="Get job statistics summary",
    description="Get summary statistics about jobs.",
)
def get_job_stats(
    service: JobService = Depends(get_service),
) -> dict[str, int | float | None]:
    """
    Get summary statistics about jobs.

    Includes:
    - Total jobs
    - Total companies
    - Total countries
    - Total skills
    - Average salary (min and max)
    - Technology role count
    """
    logger.debug("Fetching job statistics")

    stats = service.get_stats()

    logger.info("Retrieved job statistics")
    return stats


# ============================================================
# Dynamic routes last (path parameters)
# ============================================================


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job by ID",
    description="Get a single job by its UUID.",
)
def get_job(
    job_id: UUID = Path(..., description="Job UUID"), service: JobService = Depends(get_service)
):
    """
    Get a single job by ID.
    """
    logger.debug(f"Fetching job: {job_id}")

    job = service.get_job(job_id)

    if not job:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with ID {job_id} not found"
        )

    logger.info(f"Retrieved job: {job_id}")
    return JobResponse.from_model(job)


# ============================================================
# Sprint 6.6: Translation Endpoint
# ============================================================


@router.post(
    "/{job_id}/translate",
    status_code=status.HTTP_200_OK,
    summary="Translate job description",
    description="Translate a job posting to English on demand.",
)
async def translate_job(
    job_id: UUID = Path(..., description="Job UUID"),
    target_language: str = Query(
        "en",
        min_length=2,
        max_length=2,
        description="Target language code (default: en)",
    ),
    db: Session = Depends(get_db),
    service: JobService = Depends(get_service),
):
    """
    Translate a job posting to the target language.
    
    This endpoint translates the job title and description on demand.
    Translation is not stored - it's performed and returned to the client.
    
    Args:
        job_id: UUID of the job to translate
        target_language: Target language code (default: 'en')
        
    Returns:
        Translation result with original and translated text
    """
    logger.debug(f"Translating job: {job_id} to {target_language}")

    # Get the job
    job = service.get_job(job_id)
    if not job:
        logger.warning(f"Job not found for translation: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found",
        )

    # Check if translation is needed
    if job.language == target_language:
        logger.debug(f"Job {job_id} already in target language: {target_language}")
        return {
            "job_id": str(job.id),
            "source_language": job.language,
            "target_language": target_language,
            "needs_translation": False,
            "message": f"Job is already in {target_language}",
            "original_title": job.title,
            "original_description": job.description,
            "translated_title": job.title,
            "translated_description": job.description,
        }

    # Get translation service
    translation_service = await get_translation_service()

    try:
        # Translate the job
        translated = await translation_service.translate(
            text=job.description or "",
            source_language=job.language or "en",
            target_language=target_language,
        )

        logger.info(f"Translated job {job_id} from {job.language} to {target_language}")

        return {
            "job_id": str(job.id),
            "source_language": job.language,
            "target_language": target_language,
            "needs_translation": True,
            "original_title": job.title,
            "original_description": job.description,
            "translated_title": translated.text if translated.success else job.title,
            "translated_description": translated.text if translated.success else job.description,
            "success": translated.success,
            "duration_ms": translated.duration_ms,
            "character_count": translated.character_count,
            "error": str(translated.error) if translated.error else None,
        }

    except Exception as e:
        logger.error(f"Translation failed for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}",
        )