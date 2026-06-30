# app/repositories/job_repository.py
"""Job repository for database operations."""

from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.etl.validators import JobValidated
from app.models.job import Job


class JobRepository:
    """Repository for Job model operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def exists(self, source_site: str, source_id: str) -> bool:
        """Check if a job exists by source_site and source_id."""
        return self.session.query(Job).filter(
            Job.source_site == source_site,
            Job.source_id == source_id
        ).first() is not None
    
    def get_by_source(self, source_site: str, source_id: str) -> Optional[Job]:
        """Get a job by its source site and ID."""
        return self.session.query(Job).filter(
            Job.source_site == source_site,
            Job.source_id == source_id
        ).first()
    
    def create_from_validated(self, job: JobValidated) -> Job:
        """
        Create a new job from a validated job model.
        
        The repository handles mapping from the validated model
        to the ORM model.
        """
        db_job = Job(
            # Core fields
            title=job.title,
            description=job.description or "",
            company_name=job.company_name or "Unknown",
            
            # Location
            location=job.location,
            
            # Compensation
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.currency,
            
            # Source tracking (unique constraint)
            source_site=job.source,  # "adzuna"
            source_id=job.external_id,  # Adzuna's job ID
            source_url=str(job.source_url) if job.source_url else "",
            
            # Dates
            posted_date=job.posted_date,
            scraped_date=datetime.now(timezone.utc),
            
            # Status
            is_active=True,
            is_deleted=False,
        )
        
        self.session.add(db_job)
        self.session.flush()
        return db_job