"""Unit tests for API dependency injection functions."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.api.dependencies import (
    get_analytics,
    get_analytics_repository,
    get_analytics_service,
    get_db_session,
    get_job_repository,
    get_job_service,
    get_jobs_service,
    get_pipeline_run_repository,
    get_skill_repository,
    get_translation,
    get_translation_service,
)
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.job_repository import JobRepository
from app.repositories.pipeline_run_repository import PipelineRunRepository
from app.repositories.skill_repository import SkillRepository
from app.services.analytics_service import AnalyticsService
from app.services.job_service import JobService


class TestRepositoryDependencies:
    def test_get_job_repository(self):
        db = Mock()

        result = get_job_repository(db)

        assert isinstance(result, JobRepository)
        assert result.session is db

    def test_get_analytics_repository(self):
        db = Mock()

        result = get_analytics_repository(db)

        assert isinstance(result, AnalyticsRepository)
        assert result.db is db

    def test_get_skill_repository(self):
        db = Mock()

        result = get_skill_repository(db)

        assert isinstance(result, SkillRepository)
        assert result.db is db

    def test_get_pipeline_run_repository(self):
        db = Mock()

        result = get_pipeline_run_repository(db)

        assert isinstance(result, PipelineRunRepository)
        assert result.session is db


class TestServiceDependencies:
    def test_get_job_service(self):
        repository = Mock(spec=JobRepository)

        result = get_job_service(repository)

        assert isinstance(result, JobService)
        assert result.repo is repository

    def test_get_analytics_service(self):
        repository = Mock(spec=AnalyticsRepository)

        result = get_analytics_service(repository)

        assert isinstance(result, AnalyticsService)
        assert result.repo is repository


class TestTranslationDependency:
    @pytest.mark.asyncio
    async def test_get_translation_service_passes_arguments(self):
        config = Mock()
        expected_service = Mock()

        with patch(
            "app.api.dependencies.get_translation_service_instance",
            new=AsyncMock(return_value=expected_service),
        ) as mock_get_service:
            result = await get_translation_service(
                config=config,
                enable_cache=False,
                cache_max_size=250,
                cache_ttl=60,
            )

        assert result is expected_service
        mock_get_service.assert_awaited_once_with(
            config=config,
            enable_cache=False,
            cache_max_size=250,
            cache_ttl=60,
        )

    @pytest.mark.asyncio
    async def test_get_translation_service_uses_defaults(self):
        expected_service = Mock()

        with patch(
            "app.api.dependencies.get_translation_service_instance",
            new=AsyncMock(return_value=expected_service),
        ) as mock_get_service:
            result = await get_translation_service()

        assert result is expected_service
        mock_get_service.assert_awaited_once_with(
            config=None,
            enable_cache=True,
            cache_max_size=1000,
            cache_ttl=None,
        )


class TestDependencyAliases:
    def test_db_session_alias(self):
        from app.database.session import get_db

        assert get_db_session is get_db

    def test_jobs_service_alias(self):
        assert get_jobs_service is get_job_service

    def test_analytics_alias(self):
        assert get_analytics is get_analytics_service

    def test_translation_alias(self):
        assert get_translation is get_translation_service