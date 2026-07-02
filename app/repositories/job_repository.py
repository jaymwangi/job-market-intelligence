# app/repositories/job_repository.py
"""Job repository for database operations."""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from uuid import UUID

from app.etl.validators import JobValidated
from app.models.job import Job
from app.schemas.job import JobFilters


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

    # NEW: Query methods for API
    def _apply_filters(self, query, filters: JobFilters, search_query: Optional[str] = None):
        """
        Apply filters and search to the query.
        
        Args:
            query: SQLAlchemy query object
            filters: JobFilters object
            search_query: Optional search string for title/company
            
        Returns:
            Modified query with filters applied
        """
        # Apply company filter
        if filters.company_name:
            query = query.filter(Job.company_name.ilike(f"%{filters.company_name}%"))
        
        # Apply location filter
        if filters.location:
            query = query.filter(Job.location.ilike(f"%{filters.location}%"))
        
        # Apply source filter
        if filters.source_site:
            query = query.filter(Job.source_site == filters.source_site)
        
        # Apply salary range filters
        if filters.min_salary is not None:
            query = query.filter(Job.salary_max >= filters.min_salary)
        
        if filters.max_salary is not None:
            query = query.filter(Job.salary_min <= filters.max_salary)
        
        # Apply search query (title OR company)
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                or_(
                    Job.title.ilike(search_pattern),
                    Job.company_name.ilike(search_pattern)
                )
            )
        
        # Only show active, non-deleted jobs
        query = query.filter(Job.is_active == True, Job.is_deleted == False)
        
        return query

    def get_jobs(
        self, 
        filters: JobFilters, 
        offset: int, 
        limit: int, 
        search_query: Optional[str] = None
    ) -> List[Job]:
        """
        Get paginated jobs with filters and search.
        
        Args:
            filters: JobFilters object
            offset: Number of records to skip
            limit: Maximum records to return
            search_query: Optional search string
            
        Returns:
            List of Job objects
        """
        query = self.session.query(Job)
        query = self._apply_filters(query, filters, search_query)
        
        return (
            query.order_by(Job.posted_date.desc(), Job.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_jobs(
        self, 
        filters: JobFilters, 
        search_query: Optional[str] = None
    ) -> int:
        """
        Count total jobs matching filters and search.
        
        Args:
            filters: JobFilters object
            search_query: Optional search string
            
        Returns:
            Total count of matching jobs
        """
        query = self.session.query(Job)
        query = self._apply_filters(query, filters, search_query)
        
        return query.count()

    def get_by_id(self, job_id: UUID) -> Optional[Job]:
        """
        Get a single job by ID.
        
        Args:
            job_id: Job ID to retrieve
            
        Returns:
            Job object or None if not found
        """
        return self.session.query(Job).filter(
            Job.id == job_id,
            Job.is_active == True,
            Job.is_deleted == False
        ).first()