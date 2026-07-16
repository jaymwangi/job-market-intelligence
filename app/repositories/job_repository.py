"""Job repository for database operations."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.etl.validators import JobValidated
from app.models.job import Job
from app.schemas.job import JobFilters


class JobRepository:
    """Repository for Job model operations."""

    def __init__(self, session: Session):
        self.session = session

    # ============================================================
    # ETL Methods
    # ============================================================

    def _to_decimal(self, value: float | None) -> Decimal | None:
        """Convert float to Decimal for database storage."""
        if value is None:
            return None
        return Decimal(str(value))

    def _build_job_dict(self, job: JobValidated) -> dict:
        """Build a dictionary of job fields for database operations."""
        now = datetime.now(UTC)
        return {
            "title": job.title,
            "description": job.description or "",
            "company_name": job.company_name or "Unknown",
            "location": job.location,
            "salary_min": self._to_decimal(job.salary_min),
            "salary_max": self._to_decimal(job.salary_max),
            "salary_currency": job.currency,
            "source_site": job.source,
            "source_id": job.external_id,
            "source_url": str(job.source_url) if job.source_url else "",
            "posted_date": job.posted_date,
            "scraped_date": now,
            "is_active": True,
            "is_deleted": False,
        }

    def upsert_from_validated(self, job: JobValidated) -> Job:
        """
        Upsert a single validated job using PostgreSQL's ON CONFLICT.

        If a job with the same source_site and source_id exists, update it.
        Otherwise, insert a new job.

        This uses a single database operation with no prior SELECT.
        The conflict resolution is handled entirely by PostgreSQL.

        Args:
            job: Validated JobValidated object

        Returns:
            Job: The persisted Job instance
            
        Note:
            Caller owns the transaction. This method only executes SQL.
        """
        job_dict = self._build_job_dict(job)

        # Build the INSERT statement with ON CONFLICT
        stmt = insert(Job).values(**job_dict)

        # Define what to update on conflict
        # Exclude primary key, timestamps, and conflict columns from update
        update_columns = {
            "title": stmt.excluded.title,
            "description": stmt.excluded.description,
            "company_name": stmt.excluded.company_name,
            "location": stmt.excluded.location,
            "salary_min": stmt.excluded.salary_min,
            "salary_max": stmt.excluded.salary_max,
            "salary_currency": stmt.excluded.salary_currency,
            "source_url": stmt.excluded.source_url,
            "posted_date": stmt.excluded.posted_date,
            "scraped_date": stmt.excluded.scraped_date,
            "is_active": stmt.excluded.is_active,
            "is_deleted": stmt.excluded.is_deleted,
        }

        # Specify the conflict target: unique constraint on source_site + source_id
        stmt = stmt.on_conflict_do_update(
            constraint="uq_job_source_site_source_id",  # Name of the unique constraint
            set_=update_columns,
        ).returning(Job)

        # Execute and return the affected row
        result = self.session.execute(stmt)
        
        # Get the single result and merge it into the session
        # This ensures the object is properly tracked by SQLAlchemy
        job_instance = result.scalar_one()
        
        # If the job was inserted, it's already in the session.
        # If it was updated, we need to merge it to ensure the session
        # has the latest data.
        if job_instance.id:
            # Merge ensures the object is attached to the session
            # and any pending changes are resolved
            merged_job = self.session.merge(job_instance)
            return merged_job
        
        return job_instance

    def delete_jobs_older_than(self, cutoff_date: datetime) -> int:
        """
        Delete jobs whose scraped_date is older than the cutoff.

        Uses synchronize_session=False for efficiency since we don't need
        to sync these deletions back to the session.

        Args:
            cutoff_date: Delete jobs with scraped_date older than this.

        Returns:
            Number of deleted rows.
        """
        result = (
            self.session.query(Job)
            .filter(Job.scraped_date < cutoff_date)
            .delete(synchronize_session=False)
        )
        return result

    # ============================================================
    # API Query Methods
    # ============================================================

    def _apply_filters(self, query, filters: JobFilters, search_query: str | None = None):
        if filters.company_name:
            query = query.filter(Job.company_name.ilike(f"%{filters.company_name}%"))

        if filters.location:
            query = query.filter(Job.location.ilike(f"%{filters.location}%"))

        if filters.source_site:
            query = query.filter(Job.source_site == filters.source_site)

        if filters.min_salary is not None:
            query = query.filter(Job.salary_max >= filters.min_salary)

        if filters.max_salary is not None:
            query = query.filter(Job.salary_min <= filters.max_salary)

        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                or_(Job.title.ilike(search_pattern), Job.company_name.ilike(search_pattern))
            )

        query = query.filter(Job.is_active == True, Job.is_deleted == False)
        return query

    def get_jobs(
        self, filters: JobFilters, offset: int, limit: int, search_query: str | None = None
    ) -> list[Job]:
        query = self.session.query(Job)
        query = self._apply_filters(query, filters, search_query)
        return (
            query.order_by(Job.posted_date.desc(), Job.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_jobs(self, filters: JobFilters, search_query: str | None = None) -> int:
        query = self.session.query(Job)
        query = self._apply_filters(query, filters, search_query)
        return query.count()

    def get_by_id(self, job_id: UUID) -> Job | None:
        return (
            self.session.query(Job)
            .filter(Job.id == job_id, Job.is_active == True, Job.is_deleted == False)
            .first()
        )