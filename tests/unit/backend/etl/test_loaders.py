"""
Unit tests for ETL job loader.
"""

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from app.etl.loaders.job_loader import (
    JobLoader,
    LoadResult,
    SkillResult,
    UpsertResult,
)
from app.etl.schemas.validated import JobValidated


class TestJobLoader:
    """Test suite for JobLoader."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock()

    @pytest.fixture
    def loader(self, mock_db):
        """Create a JobLoader instance."""
        return JobLoader(mock_db)

    @pytest.fixture
    def valid_jobs(self):
        """Create validated job objects."""
        return [
            JobValidated(
                source="test_source",
                source_id="job_1",
                title="Python Developer",
                company="TechCorp",
                location="Remote",
                description="Test job",
                salary_currency="USD",
                url="https://example.com/job/1",
                posted_date=datetime.now(UTC),
            ),
            JobValidated(
                source="test_source",
                source_id="job_2",
                title="Data Engineer",
                company="DataInc",
                location="NY",
                description="Test job 2",
                salary_currency="USD",
                url="https://example.com/job/2",
                posted_date=datetime.now(UTC),
            ),
        ]

    @pytest.fixture
    def mock_job_repo(self):
        """Create a mock job repository."""
        return Mock()

    @pytest.fixture
    def no_existing_jobs(self, mock_db):
        """Configure database queries to return no existing records."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        return mock_db

    def test_init(self, loader, mock_db):
        """Test loader initialization."""
        assert loader.db_session == mock_db

    def test_load_result_defaults(self):
        """Test LoadResult default values."""
        result = LoadResult()

        assert result.processed == 0
        assert result.inserted == 0
        assert result.updated == 0
        assert result.purged == 0
        assert result.skills_added == 0
        assert result.relationships_added == 0
        assert result.errors == []

    def test_upsert_result_defaults(self):
        """Test UpsertResult default values."""
        result = UpsertResult()

        assert result.inserted == 0
        assert result.updated == 0

    def test_skill_result_defaults(self):
        """Test SkillResult default values."""
        result = SkillResult()

        assert result.skills_added == 0
        assert result.relationships_added == 0

    def test_upsert_empty_list(self, loader, mock_db):
        """Test upserting an empty list."""
        result = loader.upsert_in_batches([])

        assert isinstance(result, LoadResult)
        assert result.processed == 0
        assert result.inserted == 0
        assert result.updated == 0
        assert result.purged == 0
        assert result.skills_added == 0
        assert result.relationships_added == 0
        assert result.errors == []

        mock_db.flush.assert_not_called()

    def test_upsert_new_jobs(
        self,
        loader,
        valid_jobs,
        no_existing_jobs,
        mock_job_repo,
    ):
        """Test inserting new jobs."""
        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                result = loader.upsert_in_batches(valid_jobs)

        assert result.processed == 2
        assert result.inserted == 2
        assert result.updated == 0
        assert result.skills_added == 0
        assert result.relationships_added == 0
        assert result.purged == 0
        assert result.errors == []

        assert mock_job_repo.upsert_from_validated.call_count == 2
        no_existing_jobs.flush.assert_called()

    def test_upsert_existing_jobs(
        self,
        loader,
        valid_jobs,
        mock_db,
        mock_job_repo,
    ):
        """Test updating existing jobs."""
        existing_job_1 = Mock()
        existing_job_1.source_site = "test_source"
        existing_job_1.source_id = "job_1"

        existing_job_2 = Mock()
        existing_job_2.source_site = "test_source"
        existing_job_2.source_id = "job_2"

        mock_db.query.return_value.filter.return_value.all.return_value = [
            existing_job_1,
            existing_job_2,
        ]

        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                result = loader.upsert_in_batches(valid_jobs)

        assert result.processed == 2
        assert result.inserted == 0
        assert result.updated == 2
        assert result.errors == []

        assert mock_job_repo.upsert_from_validated.call_count == 2

    def test_upsert_mixed_new_and_existing_jobs(
        self,
        loader,
        valid_jobs,
        mock_db,
        mock_job_repo,
    ):
        """Test loading a mixture of new and existing jobs."""
        existing_job = Mock()
        existing_job.source_site = "test_source"
        existing_job.source_id = "job_1"

        mock_db.query.return_value.filter.return_value.all.return_value = [
            existing_job
        ]

        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                result = loader.upsert_in_batches(valid_jobs)

        assert result.processed == 2
        assert result.inserted == 1
        assert result.updated == 1
        assert result.errors == []

        assert mock_job_repo.upsert_from_validated.call_count == 2

    def test_upsert_does_not_commit(
        self,
        loader,
        valid_jobs,
        no_existing_jobs,
        mock_job_repo,
    ):
        """Test that the loader does not commit transactions."""
        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                loader.upsert_in_batches(valid_jobs)

        no_existing_jobs.commit.assert_not_called()

    def test_upsert_does_not_rollback(
        self,
        loader,
        valid_jobs,
        no_existing_jobs,
        mock_job_repo,
    ):
        """Test that the loader does not rollback transactions."""
        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                loader.upsert_in_batches(valid_jobs)

        no_existing_jobs.rollback.assert_not_called()

    def test_upsert_flushes_database(
        self,
        loader,
        valid_jobs,
        no_existing_jobs,
        mock_job_repo,
    ):
        """Test that the loader flushes database changes."""
        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                loader.upsert_in_batches(valid_jobs)

        no_existing_jobs.flush.assert_called()

    def test_upsert_in_batches(
        self,
        loader,
        valid_jobs,
        no_existing_jobs,
        mock_job_repo,
    ):
        """Test processing jobs in multiple batches."""
        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                result = loader.upsert_in_batches(
                    valid_jobs,
                    batch_size=1,
                )

        assert result.processed == 2
        assert result.inserted == 2
        assert result.updated == 0
        assert mock_job_repo.upsert_from_validated.call_count == 2

    def test_upsert_database_error_propagates(
        self,
        loader,
        valid_jobs,
        mock_db,
        mock_job_repo,
    ):
        """Test that database errors propagate to the caller."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        mock_job_repo.upsert_from_validated.side_effect = Exception(
            "Database error"
        )

        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                with pytest.raises(Exception, match="Database error"):
                    loader.upsert_in_batches(valid_jobs)

        mock_db.commit.assert_not_called()
        mock_db.rollback.assert_not_called()

    def test_to_metrics(self, loader):
        """Test conversion from LoadResult to PipelineMetrics."""
        result = LoadResult(
            processed=10,
            inserted=6,
            updated=4,
            purged=2,
            skills_added=8,
            relationships_added=15,
        )

        metrics = loader.to_metrics(result)

        assert metrics.inserted == 6
        assert metrics.updated == 4
        assert metrics.purged == 2
        assert metrics.skills_added == 8
        assert metrics.relationships_added == 15

    def test_to_metrics_ignores_errors(self, loader):
        """Test that LoadResult errors are not included in PipelineMetrics."""
        result = LoadResult(
            processed=5,
            inserted=3,
            updated=2,
            errors=["example error"],
        )

        metrics = loader.to_metrics(result)

        assert metrics.inserted == 3
        assert metrics.updated == 2
        assert metrics.purged == 0
        assert metrics.skills_added == 0
        assert metrics.relationships_added == 0

