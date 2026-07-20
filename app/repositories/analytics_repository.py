"""
Analytics Repository Module

This module provides read-only aggregation queries for job market analytics.
All queries are optimized to run directly on PostgreSQL.
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import Date, cast, desc, func
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.skill import Skill


class AnalyticsRepository:
    """
    Repository for analytics queries on job market data.

    All methods are read-only and return raw query results or ORM models.
    No business logic, formatting, or presentation concerns.
    """

    def __init__(self, db: Session):
        self.db = db

    # ============ Helper Methods ============

    def _apply_source_filter(self, query, source_site: str | None = None):
        """Apply source_site filter if provided."""
        if source_site:
            return query.filter(Job.source_site == source_site)
        return query

    def _apply_active_filter(self, query):
        """Apply active and non-deleted filter."""
        return query.filter(Job.is_active == True, Job.is_deleted == False)

    def _apply_country_filter(self, query, country_code: str | None = None):
        """Apply country code filter if provided."""
        if country_code:
            return query.filter(Job.country_code == country_code.upper())
        return query

    # ============ Sprint 3.1 Methods ============

    def get_top_skills(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get the most frequently mentioned skills in job postings.

        Args:
            limit: Maximum number of skills to return

        Returns:
            List of dicts with skill and count
        """
        query = (
            self.db.query(
                Skill.name.label("skill"),
                func.count(JobSkill.job_id).label("count"),
            )
            .join(JobSkill, Skill.id == JobSkill.skill_id)
            .join(Job, Job.id == JobSkill.job_id)
        )
        query = self._apply_active_filter(query)

        results = (
            query.group_by(Skill.id, Skill.name)
            .order_by(desc("count"))
            .limit(limit)
            .all()
        )
        return [{"skill": r.skill, "count": r.count} for r in results]

    def get_top_companies(
        self, limit: int = 10, source_site: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get companies with the most job postings.

        Args:
            limit: Maximum number of companies to return
            source_site: Optional filter by source site

        Returns:
            List of dicts with company and job_count
        """
        query = self.db.query(
            Job.company_name.label("company"),
            func.count(Job.id).label("job_count"),
        ).filter(Job.company_name.isnot(None))
        query = self._apply_active_filter(query)
        query = self._apply_source_filter(query, source_site)

        results = (
            query.group_by(Job.company_name)
            .order_by(desc("job_count"))
            .limit(limit)
            .all()
        )
        return [{"company": r.company, "job_count": r.job_count} for r in results]

    def get_jobs_by_location(
        self, limit: int = 10, source_site: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get job distribution by location.

        Args:
            limit: Maximum number of locations to return
            source_site: Optional filter by source site

        Returns:
            List of dicts with location and job_count
        """
        query = self.db.query(
            Job.location.label("location"),
            func.count(Job.id).label("job_count"),
        ).filter(Job.location.isnot(None))
        query = self._apply_active_filter(query)
        query = self._apply_source_filter(query, source_site)

        results = (
            query.group_by(Job.location)
            .order_by(desc("job_count"))
            .limit(limit)
            .all()
        )
        return [{"location": r.location, "job_count": r.job_count} for r in results]

    def get_salary_statistics(self) -> dict[str, Any]:
        """
        Compute salary statistics from job postings with salary data.

        Returns:
            Dictionary with average, min, max, median, sample_size, currency
        """
        query = self.db.query(
            func.avg(Job.salary_min).label("average"),
            func.min(Job.salary_min).label("minimum"),
            func.max(Job.salary_max).label("maximum"),
            func.count(Job.id).label("sample_size"),
            Job.salary_currency.label("currency"),
        ).filter(
            Job.salary_min.isnot(None),
            Job.salary_max.isnot(None),
        )
        query = self._apply_active_filter(query)

        stats = (
            query.group_by(Job.salary_currency)
            .order_by(desc("sample_size"))
            .first()
        )

        if not stats:
            return {
                "average": None,
                "minimum": None,
                "maximum": None,
                "median": None,
                "sample_size": 0,
                "currency": None,
            }

        # Calculate median
        median_query = self.db.query(Job.salary_min).filter(
            Job.salary_min.isnot(None)
        )
        median_query = self._apply_active_filter(median_query)
        salaries = median_query.order_by(Job.salary_min).all()

        median = None
        if salaries:
            mid = len(salaries) // 2
            median = (
                salaries[mid][0]
                if len(salaries) % 2 == 1
                else (salaries[mid - 1][0] + salaries[mid][0]) / 2
            )

        return {
            "average": float(stats.average) if stats.average else None,
            "minimum": float(stats.minimum) if stats.minimum else None,
            "maximum": float(stats.maximum) if stats.maximum else None,
            "median": median,
            "sample_size": stats.sample_size or 0,
            "currency": stats.currency or "USD",
        }

    def get_employment_type_distribution(self) -> list[dict[str, Any]]:
        """
        Get job distribution by employment type.

        Returns:
            List of dicts with employment_type and count
        """
        query = self.db.query(
            Job.employment_type.label("employment_type"),
            func.count(Job.id).label("count"),
        ).filter(Job.employment_type.isnot(None))
        query = self._apply_active_filter(query)

        results = (
            query.group_by(Job.employment_type)
            .order_by(desc("count"))
            .all()
        )
        return [
            {"employment_type": r.employment_type or "Unknown", "count": r.count}
            for r in results
        ]

    # ============ Sprint 3.2 Methods ============

    def get_salary_by_location(
        self, limit: int = 10, source_site: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Calculate average salary grouped by location.

        Args:
            limit: Maximum number of locations to return
            source_site: Optional filter by source site

        Returns:
            List of dicts with location, average_salary, job_count, min_salary, max_salary
        """
        avg_salary = (Job.salary_min + Job.salary_max) / 2

        query = self.db.query(
            Job.location.label("location"),
            func.avg(avg_salary).label("average_salary"),
            func.count(Job.id).label("job_count"),
            func.min(Job.salary_min).label("min_salary"),
            func.max(Job.salary_max).label("max_salary"),
        ).filter(
            Job.location.isnot(None),
            Job.salary_min.isnot(None),
            Job.salary_max.isnot(None),
        )
        query = self._apply_active_filter(query)
        query = self._apply_source_filter(query, source_site)

        results = (
            query.group_by(Job.location)
            .order_by(desc("job_count"))
            .limit(limit)
            .all()
        )
        return [
            {
                "location": r.location,
                "average_salary": float(r.average_salary) if r.average_salary else None,
                "job_count": r.job_count,
                "min_salary": float(r.min_salary) if r.min_salary else None,
                "max_salary": float(r.max_salary) if r.max_salary else None,
            }
            for r in results
        ]

    def get_salary_by_company(
        self, limit: int = 10, source_site: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Calculate average salary grouped by company.

        Args:
            limit: Maximum number of companies to return
            source_site: Optional filter by source site

        Returns:
            List of dicts with company, average_salary, job_count, min_salary, max_salary
        """
        avg_salary = (Job.salary_min + Job.salary_max) / 2

        query = self.db.query(
            Job.company_name.label("company"),
            func.avg(avg_salary).label("average_salary"),
            func.count(Job.id).label("job_count"),
            func.min(Job.salary_min).label("min_salary"),
            func.max(Job.salary_max).label("max_salary"),
        ).filter(
            Job.company_name.isnot(None),
            Job.salary_min.isnot(None),
            Job.salary_max.isnot(None),
        )
        query = self._apply_active_filter(query)
        query = self._apply_source_filter(query, source_site)

        results = (
            query.group_by(Job.company_name)
            .order_by(desc("job_count"))
            .limit(limit)
            .all()
        )
        return [
            {
                "company": r.company,
                "average_salary": float(r.average_salary) if r.average_salary else None,
                "job_count": r.job_count,
                "min_salary": float(r.min_salary) if r.min_salary else None,
                "max_salary": float(r.max_salary) if r.max_salary else None,
            }
            for r in results
        ]

    def get_jobs_posted_by_date(self, days: int = 30) -> list[dict[str, Any]]:
        """
        Get job posting count grouped by posted date.

        Args:
            days: Number of days to look back

        Returns:
            List of dicts with date and count
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        query = self.db.query(
            cast(Job.posted_date, Date).label("date"),
            func.count(Job.id).label("count"),
        ).filter(
            Job.posted_date >= cutoff_date,
            Job.posted_date.isnot(None),
        )
        query = self._apply_active_filter(query)

        results = (
            query.group_by(cast(Job.posted_date, Date))
            .order_by(cast(Job.posted_date, Date).asc())
            .all()
        )
        return [{"date": str(r.date), "count": r.count} for r in results]

    def get_recent_jobs(
        self, days: int = 30, limit: int = 20, source_site: str | None = None
    ) -> list[Job]:
        """
        Retrieve jobs posted within the last N days.

        Returns ORM Job objects.

        Args:
            days: Number of days to look back
            limit: Maximum number of jobs to return
            source_site: Optional filter by source site

        Returns:
            List of Job ORM models
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        query = self.db.query(Job).filter(
            Job.posted_date >= cutoff_date,
            Job.posted_date.isnot(None),
        )
        query = self._apply_active_filter(query)
        query = self._apply_source_filter(query, source_site)

        return query.order_by(Job.posted_date.desc()).limit(limit).all()

    def get_salary_distribution(self) -> list[dict[str, Any]]:
        """
        Get salary distribution by ranges.

        Returns:
            List of dicts with range and count
        """
        ranges = [
            (0, 30000, "0-30K"),
            (30000, 50000, "30K-50K"),
            (50000, 70000, "50K-70K"),
            (70000, 90000, "70K-90K"),
            (90000, 120000, "90K-120K"),
            (120000, 150000, "120K-150K"),
            (150000, 200000, "150K-200K"),
            (200000, float("inf"), "200K+"),
        ]

        results = []
        for min_val, max_val, label in ranges:
            query = self.db.query(func.count(Job.id)).filter(
                Job.salary_min.isnot(None),
                Job.salary_min >= min_val,
            )
            if max_val != float("inf"):
                query = query.filter(Job.salary_min < max_val)
            query = self._apply_active_filter(query)

            count = query.scalar() or 0
            results.append({"range": label, "count": count})

        return results

    # ============ Sprint 3.3 Methods ============

    def get_total_jobs(self) -> int:
        """Get total number of active jobs in the database."""
        query = self.db.query(Job)
        query = self._apply_active_filter(query)
        return query.count()

    def count_recent_jobs(self, days: int = 30) -> int:
        """
        Count jobs posted within the last N days.

        Args:
            days: Number of days to look back

        Returns:
            Count of recent jobs
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        query = self.db.query(Job).filter(Job.posted_date >= cutoff_date)
        query = self._apply_active_filter(query)
        return query.count()

    def count_jobs_by_source_site(self, source_site: str) -> int:
        """Count jobs from a specific source site efficiently."""
        query = self.db.query(Job).filter(Job.source_site == source_site)
        query = self._apply_active_filter(query)
        return query.count()

    def get_jobs_with_company_count(self) -> int:
        """Get count of jobs with company name populated."""
        query = self.db.query(Job).filter(Job.company_name.isnot(None))
        query = self._apply_active_filter(query)
        return query.count()

    def get_jobs_with_location_count(self) -> int:
        """Get count of jobs with location populated."""
        query = self.db.query(Job).filter(Job.location.isnot(None))
        query = self._apply_active_filter(query)
        return query.count()

    def get_jobs_with_salary_count(self) -> int:
        """Get count of jobs with salary data populated."""
        query = self.db.query(Job).filter(Job.salary_min.isnot(None))
        query = self._apply_active_filter(query)
        return query.count()

    def get_jobs_with_employment_type_count(self) -> int:
        """Get count of jobs with employment type populated."""
        query = self.db.query(Job).filter(Job.employment_type.isnot(None))
        query = self._apply_active_filter(query)
        return query.count()

    def get_jobs_with_posted_date_count(self) -> int:
        """Get count of jobs with posted date populated."""
        query = self.db.query(Job).filter(Job.posted_date.isnot(None))
        query = self._apply_active_filter(query)
        return query.count()

    def get_distinct_source_sites(self) -> list[str]:
        """Get distinct source sites in the database."""
        query = self.db.query(Job.source_site).distinct()
        query = self._apply_active_filter(query)
        results = query.all()
        return [row[0] for row in results]

    def get_skill_relationship_count(self) -> int:
        """Get total number of skill-job relationships."""
        return self.db.query(JobSkill).count()

    def get_jobs_by_source_site(self, source_site: str) -> list[Job]:
        """Get all jobs from a specific source site."""
        query = self.db.query(Job).filter(Job.source_site == source_site)
        query = self._apply_active_filter(query)
        return query.all()

    # ============ Dataset Summary ============

    def get_dataset_summary(self) -> dict[str, Any]:
        """
        Get comprehensive dataset summary.

        Returns:
            Dictionary with total_jobs, unique_companies, unique_locations,
            unique_skills, date_range, last_updated
        """
        total_jobs = self.get_total_jobs()
        unique_companies = (
            self.db.query(Job.company_name)
            .filter(Job.company_name.isnot(None))
            .distinct()
            .count()
        )

        unique_locations = (
            self.db.query(Job.location)
            .filter(Job.location.isnot(None))
            .distinct()
            .count()
        )

        unique_skills = self.db.query(Skill).count()

        date_range = (
            self.db.query(
                func.min(Job.posted_date).label("earliest"),
                func.max(Job.posted_date).label("latest"),
            )
            .first()
        )

        return {
            "total_jobs": total_jobs,
            "unique_companies": unique_companies,
            "unique_locations": unique_locations,
            "unique_skills": unique_skills,
            "date_range": {
                "earliest": (
                    str(date_range.earliest) if date_range and date_range.earliest else None
                ),
                "latest": str(date_range.latest) if date_range and date_range.latest else None,
            },
            "last_updated": datetime.now(),
        }

    # ============================================================
    # Sprint 6.6: New Enrichment Repository Methods
    # ============================================================

    def get_enriched_top_skills(
        self,
        limit: int = 20,
        country_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get the most frequently occurring skills with optional country filter.

        Args:
            limit: Number of skills to return
            country_code: Optional country filter

        Returns:
            List of dicts with skill name and count
        """
        query = (
            self.db.query(
                Skill.name.label("skill"),
                func.count(JobSkill.job_id).label("count"),
            )
            .join(JobSkill, Skill.id == JobSkill.skill_id)
            .join(Job, Job.id == JobSkill.job_id)
        )
        query = self._apply_active_filter(query)
        query = self._apply_country_filter(query, country_code)

        results = (
            query.group_by(Skill.name)
            .order_by(desc("count"))
            .limit(limit)
            .all()
        )
        return [{"skill": r.skill, "count": r.count} for r in results]

    def get_country_distribution(self) -> list[dict[str, Any]]:
        """
        Get job distribution by country.

        Returns:
            List of dicts with country and job count
        """
        query = self.db.query(
            Job.country_code.label("country"),
            func.count(Job.id).label("count"),
        ).filter(Job.country_code.isnot(None))
        query = self._apply_active_filter(query)

        results = (
            query.group_by(Job.country_code)
            .order_by(desc("count"))
            .all()
        )
        return [{"country": r.country or "Unknown", "count": r.count} for r in results]

    def get_technology_distribution(self) -> list[dict[str, Any]]:
        """
        Get distribution of technology categories.

        Returns:
            List of dicts with category and job count
        """
        query = self.db.query(
            Job.technology_category.label("category"),
            func.count(Job.id).label("count"),
        ).filter(Job.technology_category.isnot(None))
        query = self._apply_active_filter(query)

        results = (
            query.group_by(Job.technology_category)
            .order_by(desc("count"))
            .all()
        )
        return [{"category": r.category, "count": r.count} for r in results]

    def get_enriched_salary_statistics(
        self,
        country_code: str | None = None,
    ) -> dict[str, Any]:
        """
        Get salary statistics with optional country filter.

        Args:
            country_code: Optional country filter

        Returns:
            Dict with salary statistics
        """
        query = self.db.query(
            func.avg(Job.salary_min).label("average_min"),
            func.avg(Job.salary_max).label("average_max"),
            func.min(Job.salary_min).label("minimum"),
            func.max(Job.salary_max).label("maximum"),
        ).filter(Job.salary_min.isnot(None))
        query = self._apply_active_filter(query)
        query = self._apply_country_filter(query, country_code)

        result = query.first()

        # Calculate median
        median_query = self.db.query(Job.salary_min).filter(
            Job.salary_min.isnot(None)
        )
        median_query = self._apply_active_filter(median_query)
        median_query = self._apply_country_filter(median_query, country_code)

        salaries = median_query.order_by(Job.salary_min).all()

        median = None
        if salaries:
            mid = len(salaries) // 2
            median = (
                salaries[mid][0]
                if len(salaries) % 2 == 1
                else (salaries[mid - 1][0] + salaries[mid][0]) / 2
            )

        # Handle case where result is None
        if result is None:
            return {
                "average_min": None,
                "average_max": None,
                "minimum": None,
                "maximum": None,
                "median": median,
                "currency": "USD",
            }

        return {
            "average_min": float(result.average_min) if result.average_min else None,
            "average_max": float(result.average_max) if result.average_max else None,
            "minimum": float(result.minimum) if result.minimum else None,
            "maximum": float(result.maximum) if result.maximum else None,
            "median": median,
            "currency": "USD",
        }