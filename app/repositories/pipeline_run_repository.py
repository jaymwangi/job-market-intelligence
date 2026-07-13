# app/repositories/pipeline_run_repository.py
"""Pipeline run repository for tracking ETL runs."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.pipeline_run import PipelineRun


class PipelineRunRepository:
    """Repository for PipelineRun model operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        source_site: str,
        started_at: datetime | None = None,
        status: str = "running",
    ) -> PipelineRun:
        """Create a new pipeline run."""
        if started_at is None:
            started_at = datetime.now(UTC)

        run = PipelineRun(
            source_site=source_site,
            started_at=started_at,
            status=status,
            records_processed=0,
        )
        self.session.add(run)
        self.session.flush()
        return run

    def finish(
        self,
        run: PipelineRun,
        status: str,
        records_processed: int = 0,
        error_message: str | None = None,
    ) -> PipelineRun:
        """Finish a pipeline run with results."""
        run.completed_at = datetime.now(UTC)
        run.status = status
        run.records_processed = records_processed

        # Calculate duration in seconds using local variables
        started = run.started_at
        completed = run.completed_at
        if started is not None and completed is not None:
            run.duration_seconds = (completed - started).total_seconds()

        if error_message:
            run.error_message = error_message

        self.session.flush()
        return run
