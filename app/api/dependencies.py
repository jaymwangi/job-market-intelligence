"""API dependencies for dependency injection.

This module provides dependency injection functions for FastAPI routes.
It centralizes the creation and management of service instances,
making the code more testable and maintainable.

Sprint 6.6 adds:
- Translation service dependency
- Language detection service dependency
- Technology scoring service dependency

Example:
    @router.get("/jobs")
    def get_jobs(
        service: JobService = Depends(get_job_service),
        translation: TranslationService = Depends(get_translation_service),
    ):
        ...
"""

from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.job_repository import JobRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.skill_repository import SkillRepository
from app.repositories.pipeline_run_repository import PipelineRunRepository
from app.services.job_service import JobService
from app.services.analytics_service import AnalyticsService
from app.services.translation.service import (
    TranslationService,
    get_translation_service as get_translation_service_instance,
)
from app.services.translation.interface import TranslationConfig

# ============================================================
# Repository Dependencies
# ============================================================


def get_job_repository(db: Session = Depends(get_db)) -> JobRepository:
    """Get JobRepository instance."""
    return JobRepository(db)


def get_analytics_repository(db: Session = Depends(get_db)) -> AnalyticsRepository:
    """Get AnalyticsRepository instance."""
    return AnalyticsRepository(db)


def get_skill_repository(db: Session = Depends(get_db)) -> SkillRepository:
    """Get SkillRepository instance."""
    return SkillRepository(db)


def get_pipeline_run_repository(db: Session = Depends(get_db)) -> PipelineRunRepository:
    """Get PipelineRunRepository instance."""
    return PipelineRunRepository(db)


# ============================================================
# Service Dependencies
# ============================================================


def get_job_service(
    job_repo: JobRepository = Depends(get_job_repository),
) -> JobService:
    """Get JobService instance."""
    return JobService(job_repo)


def get_analytics_service(
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository),
) -> AnalyticsService:
    """Get AnalyticsService instance."""
    return AnalyticsService(analytics_repo)


# ============================================================
# Sprint 6.6: Translation Service Dependency
# ============================================================


async def get_translation_service(
    config: Optional[TranslationConfig] = None,
    enable_cache: bool = True,
    cache_max_size: int = 1000,
    cache_ttl: Optional[int] = None,
) -> TranslationService:
    """
    Get TranslationService instance (singleton).

    Args:
        config: Optional translation configuration
        enable_cache: Whether to enable caching
        cache_max_size: Maximum cache size
        cache_ttl: Cache TTL in seconds

    Returns:
        TranslationService: The translation service instance
    """
    return await get_translation_service_instance(
        config=config,
        enable_cache=enable_cache,
        cache_max_size=cache_max_size,
        cache_ttl=cache_ttl,
    )


# ============================================================
# Convenience aliases
# ============================================================

# Short aliases for common dependencies
get_db_session = get_db
get_jobs_service = get_job_service
get_analytics = get_analytics_service
get_translation = get_translation_service