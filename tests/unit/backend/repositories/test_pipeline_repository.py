"""
Unit tests for pipeline repository.
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.repositories.pipeline_run_repository import PipelineRunRepository


class TestPipelineRunRepository:
    """Test suite for pipeline repository operations."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance with mock db."""
        return PipelineRunRepository(mock_db)

    def test_init(self, repository, mock_db):
        """Test repository initialization."""
        assert repository.session == mock_db

    def test_create_default(self, repository, mock_db):
        """Test creating a pipeline run with defaults."""
        mock_run = Mock()

        with patch("app.repositories.pipeline_run_repository.PipelineRun") as MockPipelineRun:
            MockPipelineRun.return_value = mock_run

            result = repository.create(source_site="adzuna")

            assert result == mock_run
            mock_db.add.assert_called_once_with(mock_run)
            mock_db.flush.assert_called_once()

    def test_create_with_custom_start_time(self, repository, mock_db):
        """Test creating a pipeline run with custom start time."""
        mock_run = Mock()
        start_time = datetime.now(timezone.utc)

        with patch("app.repositories.pipeline_run_repository.PipelineRun") as MockPipelineRun:
            MockPipelineRun.return_value = mock_run

            result = repository.create(
                source_site="adzuna", started_at=start_time, status="running"
            )

            assert result == mock_run
            MockPipelineRun.assert_called_once_with(
                source_site="adzuna", started_at=start_time, status="running", records_processed=0
            )

    def test_finish_success(self, repository, mock_db):
        """Test finishing a pipeline run with success."""
        mock_run = Mock()
        mock_run.started_at = datetime.now(timezone.utc)
        mock_run.completed_at = None
        mock_run.duration_seconds = None

        result = repository.finish(mock_run, status="completed", records_processed=100)

        assert result == mock_run
        assert mock_run.status == "completed"
        assert mock_run.records_processed == 100
        assert mock_run.completed_at is not None
        assert mock_run.duration_seconds is not None
        assert mock_run.error_message is None
        mock_db.flush.assert_called_once()

    def test_finish_with_error(self, repository, mock_db):
        """Test finishing a pipeline run with error."""
        mock_run = Mock()
        mock_run.started_at = datetime.now(timezone.utc)
        mock_run.completed_at = None
        mock_run.duration_seconds = None

        result = repository.finish(
            mock_run, status="failed", records_processed=50, error_message="Connection error"
        )

        assert result == mock_run
        assert mock_run.status == "failed"
        assert mock_run.records_processed == 50
        assert mock_run.error_message == "Connection error"
        mock_db.flush.assert_called_once()

    def test_finish_calculates_duration(self, repository, mock_db):
        """Test finish calculates duration correctly."""
        started = datetime.now(timezone.utc)
        mock_run = Mock()
        mock_run.started_at = started
        mock_run.completed_at = None
        mock_run.duration_seconds = None

        # Patch datetime to control the completion time
        with patch("app.repositories.pipeline_run_repository.datetime") as mock_datetime:
            completed = started.replace(
                microsecond=started.microsecond + 500000
            )  # 0.5 seconds later
            mock_datetime.now.return_value = completed
            mock_datetime.timezone = timezone

            result = repository.finish(mock_run, status="completed", records_processed=100)

            assert result == mock_run
            assert mock_run.duration_seconds == 0.5
            mock_db.flush.assert_called_once()
