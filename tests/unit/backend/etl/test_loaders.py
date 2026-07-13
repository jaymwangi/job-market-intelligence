"""
Unit tests for ETL job loader.
"""

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest
from pydantic import HttpUrl

from app.etl.loaders.job_loader import JobLoader, LoadResult
from app.etl.validators.job_schema import JobValidated


class TestJobLoader:
    """Test suite for job loader."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock()

    @pytest.fixture
    def mock_job_repo(self):
        """Create a mock job repository."""
        return Mock()

    @pytest.fixture
    def mock_pipeline_repo(self):
        """Create a mock pipeline repository."""
        return Mock()

    @pytest.fixture
    def loader(self, mock_db, mock_job_repo, mock_pipeline_repo):
        """Create loader instance with mocks."""
        with patch("app.etl.loaders.job_loader.JobRepository", return_value=mock_job_repo):
            with patch(
                "app.etl.loaders.job_loader.PipelineRunRepository", return_value=mock_pipeline_repo
            ):
                return JobLoader(mock_db, source_site="test_source")

    @pytest.fixture
    def valid_jobs(self):
        """Create validated job objects."""
        return [
            JobValidated(
                external_id="job_1",
                title="Python Developer",
                company_name="TechCorp",
                location="Remote",
                description="Test job",
                currency="USD",
                source_url=HttpUrl("https://example.com/job/1"),
                posted_date=datetime.now(UTC),
                source="test_source",
            ),  # type: ignore
            JobValidated(
                external_id="job_2",
                title="Data Engineer",
                company_name="DataInc",
                location="NY",
                description="Test job 2",
                currency="USD",
                source_url=HttpUrl("https://example.com/job/2"),
                posted_date=datetime.now(UTC),
                source="test_source",
            ),  # type: ignore
        ]

    def test_init(self, loader, mock_db):
        """Test loader initialization."""
        assert loader.db_session == mock_db
        assert loader.source_site == "test_source"
        assert loader.job_repo is not None
        assert loader.pipeline_run_repo is not None

    def test_load_success(self, loader, valid_jobs, mock_job_repo, mock_pipeline_repo):
        """Test successful loading of jobs."""
        mock_pipeline_repo.create.return_value = Mock()
        mock_job_repo.exists.return_value = False

        result = loader.load(valid_jobs)

        assert isinstance(result, LoadResult)
        assert result.processed == 2
        assert result.inserted == 2
        assert result.skipped == 0
        assert result.failed == 0
        assert result.errors == []

        mock_job_repo.create_from_validated.assert_called()
        loader.db_session.commit.assert_called_once()

    def test_load_with_duplicates(self, loader, valid_jobs, mock_job_repo, mock_pipeline_repo):
        """Test loading with duplicate jobs."""
        mock_pipeline_repo.create.return_value = Mock()
        # First job exists, second doesn't
        mock_job_repo.exists.side_effect = [True, False]

        result = loader.load(valid_jobs)

        assert result.processed == 2
        assert result.inserted == 1
        assert result.skipped == 1
        assert result.failed == 0

    def test_load_with_transaction_rollback(
        self, loader, valid_jobs, mock_job_repo, mock_pipeline_repo
    ):
        """Test transaction rollback on error."""
        mock_pipeline_repo.create.return_value = Mock()
        mock_job_repo.create_from_validated.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            loader.load(valid_jobs)

        loader.db_session.rollback.assert_called_once()
        mock_pipeline_repo.finish.assert_called()

    def test_load_empty_list(self, loader):
        """Test loading empty list."""
        result = loader.load([])

        assert isinstance(result, LoadResult)
        assert result.processed == 0
        assert result.inserted == 0
        assert result.skipped == 0
        assert result.failed == 0

    def test_load_result_tracking(self, loader, valid_jobs, mock_job_repo, mock_pipeline_repo):
        """Test load result tracking."""
        mock_pipeline_repo.create.return_value = Mock()
        mock_job_repo.exists.return_value = False

        result = loader.load(valid_jobs)

        assert isinstance(result, LoadResult)
        assert hasattr(result, "processed")
        assert hasattr(result, "inserted")
        assert hasattr(result, "skipped")
        assert hasattr(result, "failed")
        assert hasattr(result, "errors")

    def test_load_pipeline_tracking(self, loader, valid_jobs, mock_job_repo, mock_pipeline_repo):
        """Test pipeline run tracking."""
        mock_run = Mock()
        mock_pipeline_repo.create.return_value = mock_run
        mock_job_repo.exists.return_value = False

        loader.load(valid_jobs)

        mock_pipeline_repo.create.assert_called_once()
        mock_pipeline_repo.finish.assert_called_once()
