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
    - Upsert: Insert new jobs, Update existing jobs by source_site + source_id
    - Purge jobs older than retention period (based on scraped_date)
    - Use repositories for persistence
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
        Upsert validated jobs into the database.
        
        - If job exists by source_site + source_id: UPDATE
        - If job doesn't exist: INSERT
        
        Uses targeted lookup to avoid N+1 queries:
        1. Get source_ids from current batch
        2. Fetch only those that exist in one query
        3. Build a lookup dict
        4. Process each job in memory

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

        # Extract source_ids from current batch
        source_ids = list({job.external_id for job in jobs})

        # Fetch only those that exist (targeted query)
        existing_jobs = self.job_repo.get_by_source_ids(
            self.source_site, source_ids
        )
        
        # Build lookup dict
        existing_by_source_id = {job.source_id: job for job in existing_jobs}

        # Process each job
        for job in jobs:
            if job.external_id in existing_by_source_id:
                # UPDATE existing job
                existing = existing_by_source_id[job.external_id]
                self.job_repo.update_from_validated(existing, job)
                result.updated += 1
            else:
                # INSERT new job
                self.job_repo.create_from_validated(job)
                result.inserted += 1

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