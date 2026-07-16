"""Job loader for persisting validated jobs to the database."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.etl.validators import JobValidated
from app.repositories.job_repository import JobRepository


@dataclass
class LoadResult:
    """Summary of a loading operation."""

    processed: int = 0
    inserted: int = 0
    updated: int = 0
    deleted: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class JobLoader:
    """
    Loads validated jobs into the database with upsert support.

    Transaction management belongs to the caller.
    This class never commits or rolls back.
    """

    def __init__(self, db_session: Session, source_site: str = "adzuna"):
        self.db_session = db_session
        self.source_site = source_site
        self.job_repo = JobRepository(db_session)

    def upsert(self, jobs: list[JobValidated]) -> LoadResult:
        """
        Upsert validated jobs into the database using PostgreSQL ON CONFLICT.

        IMPORTANT: If any job fails, the entire transaction is aborted.
        The caller must handle rollback.

        Args:
            jobs: List of validated JobValidated objects

        Returns:
            LoadResult: Summary of the loading operation

        Raises:
            Exception: If any database operation fails
            
        Note:
            Caller owns the transaction. This method only flushes.
            Caller must commit or rollback.
        """
        result = LoadResult(processed=len(jobs))

        if not jobs:
            return result

        # FIX 2: Don't catch exceptions - let them propagate to caller
        # The caller (run_pipeline.py) handles rollback
        for job in jobs:
            self.job_repo.upsert_from_validated(job)

        # Single flush for all operations
        self.db_session.flush()

        return result

    def purge_older_than(self, retention_days: int) -> int:
        """Delete jobs older than retention period."""
        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)
        deleted_count = self.job_repo.delete_jobs_older_than(cutoff_date)
        self.db_session.flush()
        return deleted_count