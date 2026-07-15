"""Job repository for database operations."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_
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

    def get_by_source_ids(self, source_site: str, source_ids: list[str]) -> list[Job]:
        """
        Get multiple jobs by source site and source IDs.
        Used for targeted lookups during upsert to avoid N+1 queries.
        """
        if not source_ids:
            return []
            
        return (
            self.session.query(Job)
            .filter(
                Job.source_site == source_site,
                Job.source_id.in_(source_ids)
            )
            .all()
        )

    def create_from_validated(self, job: JobValidated) -> Job:
        """
        Create a new job from a validated job model.
        """
        now = datetime.now(UTC)
        
        db_job = Job(
            title=job.title,
            description=job.description or "",
            company_name=job.company_name or "Unknown",
            location=job.location,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.currency,
            source_site=job.source,
            source_id=job.external_id,
            source_url=str(job.source_url) if job.source_url else "",
            posted_date=job.posted_date,
            scraped_date=now,
            is_active=True,
            is_deleted=False,
        )

        self.session.add(db_job)
        return db_job

    def update_from_validated(self, existing: Job, job: JobValidated) -> Job:
        """
        Update an existing job from a validated job model.
        """
        now = datetime.now(UTC)
        
        existing.title = job.title
        existing.description = job.description or ""
        existing.company_name = job.company_name or "Unknown"
        existing.location = job.location
        existing.salary_min = job.salary_min
        existing.salary_max = job.salary_max
        existing.salary_currency = job.currency
        existing.source_url = str(job.source_url) if job.source_url else ""
        existing.posted_date = job.posted_date
        existing.scraped_date = now
        existing.is_active = True
        existing.is_deleted = False

        return existing

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