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

    Responsibilities:
    - Accept validated JobValidated objects
    - Use repository for PostgreSQL upsert (INSERT ... ON CONFLICT DO UPDATE)
    - Purge jobs older than retention period (based on scraped_date)
    - Track loading statistics
    
    Transaction management belongs to the caller.
    This class never commits or rolls back.
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

    def upsert(self, jobs: list[JobValidated]) -> LoadResult:
        """
        Upsert validated jobs into the database using PostgreSQL ON CONFLICT.
        
        Each job is upserted individually using INSERT ... ON CONFLICT DO UPDATE.
        PostgreSQL handles the conflict resolution - no prior SELECT needed.
        
        Since the upsert operation doesn't tell us whether it inserted or updated,
        we track processed count only. The actual insert/update counts are
        handled by the database.

        Args:
            jobs: List of validated JobValidated objects

        Returns:
            LoadResult: Summary of the loading operation
            
        Note:
            Caller owns the transaction. This method only flushes.
            Caller must commit or rollback.
        """
        result = LoadResult(processed=len(jobs))

        if not jobs:
            return result

        # Upsert each job - PostgreSQL handles insert vs update decision
        for job in jobs:
            try:
                self.job_repo.upsert_from_validated(job)
                # PostgreSQL's ON CONFLICT handles insert/update internally
                # We can't easily distinguish insert vs update from the returning clause
                # without additional complexity, so we just track processed
            except Exception as e:
                result.failed += 1
                result.errors.append(f"Failed to upsert job {job.external_id}: {str(e)}")

        # Single flush for all operations - caller decides when to commit
        self.db_session.flush()

        return result

    def purge_older_than(self, retention_days: int) -> int:
        """
        Delete jobs older than retention period.
        
        Uses scraped_date (when the job was last seen) rather than posted_date.
        This prevents jobs that are reposted from being repeatedly deleted and re-inserted.

        Args:
            retention_days: Number of days to retain jobs

        Returns:
            int: Number of jobs deleted
            
        Note:
            Caller owns the transaction. This method only flushes.
            Caller must commit or rollback.
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)
        deleted_count = self.job_repo.delete_jobs_older_than(cutoff_date)
        
        # Flush but don't commit - caller owns the transaction
        self.db_session.flush()
        
        return deleted_count