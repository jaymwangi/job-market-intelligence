# app/etl/loaders/job_loader.py
"""Job loader for persisting validated jobs to the database."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.etl.validators import JobValidated
from app.repositories.job_repository import JobRepository
from app.repositories.pipeline_run_repository import PipelineRunRepository


@dataclass
class LoadResult:
    """Summary of a loading operation."""

    processed: int = 0
    inserted: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class JobLoader:
    """
    Loads validated jobs into the database.

    Responsibilities:
    - Accept validated JobValidated objects
    - Orchestrate loading and transactions
    - Use repositories for persistence
    - Skip duplicates via source_site + source_id
    - Track loading statistics
    """

    def __init__(self, db_session: Session, source_site: str = "adzuna"):
        """
        Initialize the job loader.

        Args:
            db_session: SQLAlchemy session for database operations
            source_site: Name of the source site for tracking
        """
        self.db_session = db_session
        self.source_site = source_site
        self.job_repo = JobRepository(db_session)
        self.pipeline_run_repo = PipelineRunRepository(db_session)

    def load(self, jobs: list[JobValidated]) -> LoadResult:
        """
        Load validated jobs into the database.

        All jobs are loaded in a single transaction.
        If any job fails, the entire transaction is rolled back.

        Args:
            jobs: List of validated JobValidated objects

        Returns:
            LoadResult: Summary of the loading operation
        """
        result = LoadResult(processed=len(jobs))

        # Start pipeline run tracking
        pipeline_run = self.pipeline_run_repo.create(
            source_site=self.source_site, started_at=datetime.now(timezone.utc)
        )

        try:
            # Begin transaction - load all jobs
            for job in jobs:
                # Check if job already exists by source_site + source_id
                if self.job_repo.exists(self.source_site, job.external_id):
                    result.skipped += 1
                    continue

                # Create new job - repository handles ORM construction
                self.job_repo.create_from_validated(job)
                result.inserted += 1

            # Commit transaction
            self.db_session.commit()

            # Finish pipeline run with success
            self.pipeline_run_repo.finish(
                pipeline_run,
                status="completed",
                records_processed=result.inserted,
            )

        except Exception as e:
            # Rollback on any failure
            self.db_session.rollback()
            result.failed = result.processed - result.inserted - result.skipped
            result.errors.append(str(e))

            # Finish pipeline run with failure
            self.pipeline_run_repo.finish(
                pipeline_run,
                status="failed",
                records_processed=result.inserted,
                error_message=str(e),
            )
            raise

        return result
