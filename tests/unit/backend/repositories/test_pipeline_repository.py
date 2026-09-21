"""
Unit tests for pipeline repository.
"""

from datetime import UTC, datetime, timedelta, timezone
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
        start_time = datetime.now(UTC)

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
        mock_run.started_at = datetime.now(UTC)
        mock_run.completed_at = None
        mock_run.duration_seconds = None
        mock_run.error_message = None

        result = repository.finish(
            mock_run,
            status="completed",
            records_processed=100,
        )

        assert result == mock_run
        assert mock_run.status == "completed"
        assert mock_run.records_processed == 100
        assert mock_run.completed_at is not None
        assert mock_run.duration_seconds is not None
        assert mock_run.error_message is None

    def test_finish_with_error(self, repository, mock_db):
        """Test finishing a pipeline run with error."""
        mock_run = Mock()
        mock_run.started_at = datetime.now(UTC)
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
        started = datetime.now(UTC)
        mock_run = Mock()
        mock_run.started_at = started
        mock_run.completed_at = None
        mock_run.duration_seconds = None

        # Patch datetime to control the completion time.
        with patch("app.repositories.pipeline_run_repository.datetime") as mock_datetime:
            completed = started + timedelta(seconds=0.5)

            mock_datetime.now.return_value = completed
            mock_datetime.timezone = timezone

            result = repository.finish(
                mock_run,
                status="completed",
                records_processed=100,
            )

            assert result == mock_run
            assert mock_run.duration_seconds == 0.5
            mock_db.flush.assert_called_once()


    def test_get_latest_completed_run_returns_row(
        self,
        repository,
        mock_db,
    ):
        """Return the latest completed pipeline run as a dictionary."""
        row = (
            1,
            datetime(2026, 9, 17, 8, 0, tzinfo=UTC),
            datetime(2026, 9, 17, 8, 30, tzinfo=UTC),
            "completed",
            100,
            1800.0,
            None,
            "adzuna",
            datetime(2026, 9, 17, 8, 0, tzinfo=UTC),
            datetime(2026, 9, 17, 8, 30, tzinfo=UTC),
        )

        result = Mock()
        result.fetchone.return_value = row
        mock_db.execute.return_value = result

        output = repository.get_latest_completed_run()

        assert output == {
            "id": 1,
            "started_at": row[1],
            "completed_at": row[2],
            "status": "completed",
            "records_processed": 100,
            "duration_seconds": 1800.0,
            "error_message": None,
            "source_site": "adzuna",
            "created_at": row[8],
            "updated_at": row[9],
        }


    def test_get_latest_completed_run_returns_none_when_no_row(
        self,
        repository,
        mock_db,
    ):
        """Return None when there are no completed pipeline runs."""
        result = Mock()
        result.fetchone.return_value = None
        mock_db.execute.return_value = result

        assert repository.get_latest_completed_run() is None


    def test_get_latest_completed_run_returns_none_on_error(
        self,
        repository,
        mock_db,
    ):
        """Return None when the database query fails."""
        mock_db.execute.side_effect = RuntimeError("Database unavailable")

        assert repository.get_latest_completed_run() is None


    def test_get_running_run_returns_row(
        self,
        repository,
        mock_db,
    ):
        """Return the currently running pipeline run as a dictionary."""
        row = (
            2,
            datetime(2026, 9, 17, 9, 0, tzinfo=UTC),
            None,
            "running",
            50,
            None,
            None,
            "adzuna",
            datetime(2026, 9, 17, 9, 0, tzinfo=UTC),
            datetime(2026, 9, 17, 9, 0, tzinfo=UTC),
        )

        result = Mock()
        result.fetchone.return_value = row
        mock_db.execute.return_value = result

        output = repository.get_running_run()

        assert output == {
            "id": 2,
            "started_at": row[1],
            "completed_at": None,
            "status": "running",
            "records_processed": 50,
            "duration_seconds": None,
            "error_message": None,
            "source_site": "adzuna",
            "created_at": row[8],
            "updated_at": row[9],
        }


    def test_get_running_run_returns_none_when_no_row(
        self,
        repository,
        mock_db,
    ):
        """Return None when no pipeline run is currently running."""
        result = Mock()
        result.fetchone.return_value = None
        mock_db.execute.return_value = result

        assert repository.get_running_run() is None


    def test_get_running_run_returns_none_on_error(
        self,
        repository,
        mock_db,
    ):
        """Return None when the database query fails."""
        mock_db.execute.side_effect = RuntimeError("Database unavailable")

        assert repository.get_running_run() is None


    def test_get_last_run_time_returns_completed_time(
        self, repository
    ):
        completed_at = datetime(2026, 9, 17, 10, 30, tzinfo=UTC)
        repository.get_latest_completed_run = Mock(
            return_value={"completed_at": completed_at}
        )

        result = repository.get_last_run_time()

        assert result == completed_at

    def test_get_last_run_time_returns_started_time_when_no_completed_time(
        self, repository
    ):
        started_at = datetime(2026, 9, 17, 10, 0, tzinfo=UTC)
        repository.get_latest_completed_run = Mock(
            return_value={"started_at": started_at}
        )

        result = repository.get_last_run_time()

        assert result == started_at


    def test_get_last_run_time_returns_none_when_no_run(
        self, repository
    ):
        repository.get_latest_completed_run = Mock(return_value=None)

        result = repository.get_last_run_time()

        assert result is None

    def test_format_last_run_time_returns_no_runs_yet_when_no_run(
        self, repository
    ):
        repository.get_latest_completed_run = Mock(return_value=None)

        result = repository.format_last_run_time()

        assert result == "No runs yet"

    def test_format_last_run_time_returns_no_runs_yet_when_no_time(
        self, repository
    ):
        repository.get_latest_completed_run = Mock(
            return_value={"completed_at": None, "started_at": None}
        )

        result = repository.format_last_run_time()

        assert result == "No runs yet"

    def test_format_last_run_time_handles_invalid_date(
        self, repository
    ):
        repository.get_latest_completed_run = Mock(
            return_value={"completed_at": "not-a-date"}
        )

        result = repository.format_last_run_time()

        assert result == "Invalid date"

    def test_format_last_run_time_returns_days_and_hours(
        self, repository
    ):
        last_time = datetime.now(UTC) - timedelta(days=2, hours=3)
        repository.get_latest_completed_run = Mock(
            return_value={"completed_at": last_time}
        )

        result = repository.format_last_run_time()

        assert result.startswith("2d 3h")

    def test_format_last_run_time_returns_hours_and_minutes(
        self, repository
    ):
        last_time = datetime.now(UTC) - timedelta(hours=2, minutes=15)
        repository.get_latest_completed_run = Mock(
            return_value={"completed_at": last_time}
        )

        result = repository.format_last_run_time()

        assert result.startswith("2h 15m")

    def test_format_last_run_time_returns_minutes(
        self, repository
    ):
        last_time = datetime.now(UTC) - timedelta(minutes=15)
        repository.get_latest_completed_run = Mock(
            return_value={"completed_at": last_time}
        )

        result = repository.format_last_run_time()

        assert result.startswith("15m ago")

    def test_format_last_run_time_returns_just_now(
        self, repository
    ):
        last_time = datetime.now(UTC) - timedelta(seconds=30)
        repository.get_latest_completed_run = Mock(
            return_value={"completed_at": last_time}
        )

        result = repository.format_last_run_time()

        assert result == "Just now"

    @patch("app.repositories.pipeline_run_repository.datetime")
    def test_format_last_run_time_returns_hours_only(
        self, mock_datetime, repository
    ):
        now = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)
        last_time = datetime(2026, 9, 17, 10, 0, tzinfo=UTC)

        mock_datetime.now.return_value = now
        mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

        repository.get_latest_completed_run = Mock(
            return_value={"completed_at": last_time}
        )

        result = repository.format_last_run_time()

        assert result == "2h ago"

    def test_format_last_run_time_handles_naive_datetime(
        self, repository
    ):
        last_time = datetime.now(UTC).replace(tzinfo=None) - timedelta(
            minutes=15
        )
        repository.get_latest_completed_run = Mock(
            return_value={"completed_at": last_time}
        )

        result = repository.format_last_run_time()

        assert result.endswith("m ago")