"""Job repository for database operations."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID
from typing import TYPE_CHECKING, Any

from sqlalchemy import or_, func, desc
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.skill import Skill
from app.models.job_skill import JobSkill
from app.schemas.job import JobFilters

# Use TYPE_CHECKING to avoid circular import at runtime
if TYPE_CHECKING:
    from app.etl.schemas.validated import JobValidated

# Import at runtime using a local import inside methods instead
import logging

logger = logging.getLogger(__name__)


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

    def _build_job_dict(self, job: "JobValidated") -> dict:
        """
        Build a dictionary of job fields for database operations.
        
        Maps from JobValidated schema fields to Job model fields.
        """
        from app.etl.schemas.validated import JobValidated  # Local import to avoid circular

        now = datetime.now(UTC)
        return {
            "title": job.title,
            "description": job.description or "",
            "company_name": job.company or "Unknown",
            "location": job.location,
            "salary_min": self._to_decimal(job.salary_min),
            "salary_max": self._to_decimal(job.salary_max),
            "salary_currency": job.salary_currency,
            "source_site": job.source,
            "source_id": job.source_id,
            "source_url": job.url or "",
            "posted_date": job.posted_date,
            "scraped_date": now,
            "is_active": True,
            "is_deleted": False,
            # Sprint 6.6: Enrichment fields
            "technology_category": job.technology_category,
            "is_tech_role": job.is_tech_role,
            "country_code": job.country_code,
            "currency": job.currency,
            "employment_type": job.employment_type,
        }

    def upsert_from_validated(self, job: "JobValidated") -> Job:
        """
        Upsert a single validated job using PostgreSQL's ON CONFLICT.
        """
        from app.etl.schemas.validated import JobValidated  # Local import to avoid circular

        job_dict = self._build_job_dict(job)

        stmt = insert(Job).values(**job_dict)

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
            # Sprint 6.6: Enrichment fields
            "technology_category": stmt.excluded.technology_category,
            "is_tech_role": stmt.excluded.is_tech_role,
            "country_code": stmt.excluded.country_code,
            "currency": stmt.excluded.currency,
            "employment_type": stmt.excluded.employment_type,
        }

        stmt = stmt.on_conflict_do_update(
            constraint="uq_job_source",
            set_=update_columns,
        ).returning(Job)

        result = self.session.execute(stmt)
        return result.scalar_one()

    def delete_jobs_older_than(self, cutoff_date: datetime) -> int:
        """Delete jobs whose scraped_date is older than the cutoff."""
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

        # Sprint 6.6: New enrichment filters
        if filters.country_code:
            query = query.filter(Job.country_code == filters.country_code.upper())

        if filters.technology_category:
            query = query.filter(Job.technology_category == filters.technology_category)

        if filters.employment_type:
            query = query.filter(Job.employment_type == filters.employment_type)

        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                or_(Job.title.ilike(search_pattern), Job.company_name.ilike(search_pattern))
            )

        query = query.filter(
            Job.is_active.is_(True),
            Job.is_deleted.is_(False)
        )
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
            .filter(
                Job.id == job_id,
                Job.is_active.is_(True),
                Job.is_deleted.is_(False)
            )
            .first()
        )

    # ============================================================
    # Sprint 6.6: Analytics Methods
    # ============================================================

    def get_top_skills(
        self,
        limit: int = 20,
        country_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get the most frequently occurring skills.

        Args:
            limit: Number of skills to return
            country_code: Optional country filter

        Returns:
            List of dicts with skill name and count
        """
        query = self.session.query(
            Skill.name,
            func.count(JobSkill.job_id).label("count")
        ).join(JobSkill, Skill.id == JobSkill.skill_id)\
         .join(Job, Job.id == JobSkill.job_id)\
         .filter(
             Job.is_active.is_(True),
             Job.is_deleted.is_(False)
         )

        if country_code:
            query = query.filter(Job.country_code == country_code.upper())

        results = query.group_by(Skill.name)\
                      .order_by(desc("count"))\
                      .limit(limit)\
                      .all()

        return [{"skill": r[0], "count": r[1]} for r in results]

    def get_country_distribution(self) -> list[dict[str, Any]]:
        """
        Get job distribution by country.

        Returns:
            List of dicts with country and job count
        """
        results = self.session.query(
            Job.country_code,
            func.count(Job.id).label("count")
        ).filter(
            Job.country_code.isnot(None),
            Job.is_active.is_(True),
            Job.is_deleted.is_(False)
        ).group_by(Job.country_code)\
         .order_by(desc("count"))\
         .all()

        return [{"country": r[0] or "Unknown", "count": r[1]} for r in results]

    def get_technology_distribution(self) -> list[dict[str, Any]]:
        """
        Get distribution of technology categories.

        Returns:
            List of dicts with category and job count
        """
        results = self.session.query(
            Job.technology_category,
            func.count(Job.id).label("count")
        ).filter(
            Job.technology_category.isnot(None),
            Job.is_active.is_(True),
            Job.is_deleted.is_(False)
        ).group_by(Job.technology_category)\
         .order_by(desc("count"))\
         .all()

        return [{"category": r[0], "count": r[1]} for r in results]

    def get_stats(self) -> dict[str, Any]:
        """
        Get summary statistics about jobs.

        Returns:
            Dict with various statistics
        """
        # Total jobs
        total_jobs = self.session.query(
            func.count(Job.id)
        ).filter(
            Job.is_active.is_(True),
            Job.is_deleted.is_(False)
        ).scalar() or 0

        # Total companies
        total_companies = self.session.query(
            func.count(func.distinct(Job.company_name))
        ).filter(
            Job.company_name.isnot(None),
            Job.is_active.is_(True),
            Job.is_deleted.is_(False)
        ).scalar() or 0

        # Total countries
        total_countries = self.session.query(
            func.count(func.distinct(Job.country_code))
        ).filter(
            Job.country_code.isnot(None),
            Job.is_active.is_(True),
            Job.is_deleted.is_(False)
        ).scalar() or 0

        # Total skills
        total_skills = self.session.query(
            func.count(Skill.id)
        ).scalar() or 0

        # Average salary
        avg_min = self.session.query(
            func.avg(Job.salary_min)
        ).filter(
            Job.salary_min.isnot(None),
            Job.is_active.is_(True),
            Job.is_deleted.is_(False)
        ).scalar()

        avg_max = self.session.query(
            func.avg(Job.salary_max)
        ).filter(
            Job.salary_max.isnot(None),
            Job.is_active.is_(True),
            Job.is_deleted.is_(False)
        ).scalar()

        # Technology role count
        tech_roles = self.session.query(
            func.count(Job.id)
        ).filter(
            Job.is_tech_role.is_(True),
            Job.is_active.is_(True),
            Job.is_deleted.is_(False)
        ).scalar() or 0

        return {
            "total_jobs": total_jobs,
            "total_companies": total_companies,
            "total_countries": total_countries,
            "total_skills": total_skills,
            "average_salary_min": float(avg_min) if avg_min else None,
            "average_salary_max": float(avg_max) if avg_max else None,
            "tech_roles": tech_roles,
        }