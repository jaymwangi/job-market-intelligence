"""
Analytics Repository Module

This module provides read-only aggregation queries for job market analytics.
All queries are optimized to run directly on PostgreSQL.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, date as date_type
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date

from app.models.job import Job
from app.models.skill import Skill
from app.models.job_skill import JobSkill


class AnalyticsRepository:
    """
    Repository for analytics queries on job market data.
    
    All methods are read-only and return raw query results or ORM models.
    No business logic, formatting, or presentation concerns.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ Helper Methods ============
    
    def _apply_source_filter(self, query, source_site: Optional[str] = None):
        """Apply source_site filter if provided."""
        if source_site:
            return query.filter(Job.source_site == source_site)
        return query
    
    # ============ Sprint 3.1 Methods ============
    
    def get_top_skills(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get the most frequently mentioned skills in job postings.
        
        Args:
            limit: Maximum number of skills to return
            
        Returns:
            List of tuples (skill_name, count)
        """
        results = (
            self.db.query(
                Skill.name,
                func.count(JobSkill.job_id)
            )
            .join(JobSkill, Skill.id == JobSkill.skill_id)
            .group_by(Skill.id, Skill.name)
            .order_by(func.count(JobSkill.job_id).desc())
            .limit(limit)
            .all()
        )
        return [(row[0], row[1]) for row in results]
    
    def get_top_companies(
        self,
        limit: int = 10,
        source_site: Optional[str] = None
    ) -> List[Tuple[str, int]]:
        """
        Get companies with the most job postings.
        
        Args:
            limit: Maximum number of companies to return
            source_site: Optional filter by source site
            
        Returns:
            List of tuples (company_name, job_count)
        """
        query = (
            self.db.query(
                Job.company_name,
                func.count(Job.id)
            )
            .filter(Job.company_name.isnot(None))
        )
        query = self._apply_source_filter(query, source_site)
        
        results = (
            query
            .group_by(Job.company_name)
            .order_by(func.count(Job.id).desc())
            .limit(limit)
            .all()
        )
        return [(row[0], row[1]) for row in results]
    
    def get_jobs_by_location(
        self,
        limit: int = 10,
        source_site: Optional[str] = None
    ) -> List[Tuple[str, int]]:
        """
        Get job distribution by location.
        
        Args:
            limit: Maximum number of locations to return
            source_site: Optional filter by source site
            
        Returns:
            List of tuples (location, job_count)
        """
        query = (
            self.db.query(
                Job.location,
                func.count(Job.id)
            )
            .filter(Job.location.isnot(None))
        )
        query = self._apply_source_filter(query, source_site)
        
        results = (
            query
            .group_by(Job.location)
            .order_by(func.count(Job.id).desc())
            .limit(limit)
            .all()
        )
        return [(row[0], row[1]) for row in results]
    
    def get_salary_statistics(self) -> Dict[str, Optional[float]]:
        """
        Compute salary statistics from job postings with salary data.
        
        Returns:
            Dictionary with keys: avg_min, avg_max, min_salary, max_salary
        """
        stats = self.db.query(
            func.avg(Job.salary_min).label("avg_min"),
            func.avg(Job.salary_max).label("avg_max"),
            func.min(Job.salary_min).label("min_salary"),
            func.max(Job.salary_max).label("max_salary")
        ).first()
        
        if stats and any(getattr(stats, col) is not None for col in ['avg_min', 'avg_max']):
            return {
                "avg_min": round(float(stats.avg_min), 2) if stats.avg_min is not None else None,
                "avg_max": round(float(stats.avg_max), 2) if stats.avg_max is not None else None,
                "min_salary": float(stats.min_salary) if stats.min_salary is not None else None,
                "max_salary": float(stats.max_salary) if stats.max_salary is not None else None
            }
        
        return {
            "avg_min": None,
            "avg_max": None,
            "min_salary": None,
            "max_salary": None
        }
    
    def get_employment_type_distribution(self) -> List[Tuple[str, int]]:
        """
        Get job distribution by employment type.
        
        Returns:
            List of tuples (employment_type, job_count)
        """
        results = (
            self.db.query(
                Job.employment_type,
                func.count(Job.id)
            )
            .filter(Job.employment_type.isnot(None))
            .group_by(Job.employment_type)
            .order_by(func.count(Job.id).desc())
            .all()
        )
        return [(row[0], row[1]) for row in results]
    
    # ============ Sprint 3.2 Methods ============
    
    def get_salary_by_location(
        self,
        limit: int = 10,
        source_site: Optional[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Calculate average salary grouped by location.
        
        Args:
            limit: Maximum number of locations to return
            source_site: Optional filter by source site
            
        Returns:
            List of tuples (location, average_salary)
        """
        avg_salary = (Job.salary_min + Job.salary_max) / 2
        
        query = (
            self.db.query(
                Job.location,
                func.avg(avg_salary).label("avg_salary")
            )
            .filter(
                Job.location.isnot(None),
                Job.salary_min.isnot(None),
                Job.salary_max.isnot(None)
            )
        )
        query = self._apply_source_filter(query, source_site)
        
        results = (
            query
            .group_by(Job.location)
            .order_by(func.avg(avg_salary).desc())
            .limit(limit)
            .all()
        )
        return [(row[0], float(row[1])) for row in results]
    
    def get_salary_by_company(
        self,
        limit: int = 10,
        source_site: Optional[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Calculate average salary grouped by company.
        
        Args:
            limit: Maximum number of companies to return
            source_site: Optional filter by source site
            
        Returns:
            List of tuples (company_name, average_salary)
        """
        avg_salary = (Job.salary_min + Job.salary_max) / 2
        
        query = (
            self.db.query(
                Job.company_name,
                func.avg(avg_salary).label("avg_salary")
            )
            .filter(
                Job.company_name.isnot(None),
                Job.salary_min.isnot(None),
                Job.salary_max.isnot(None)
            )
        )
        query = self._apply_source_filter(query, source_site)
        
        results = (
            query
            .group_by(Job.company_name)
            .order_by(func.avg(avg_salary).desc())
            .limit(limit)
            .all()
        )
        return [(row[0], float(row[1])) for row in results]
    
    def get_jobs_posted_by_date(self) -> List[Tuple[date_type, int]]:
        """
        Get job posting count grouped by posted date.
        
        Returns:
            List of tuples (date, job_count) sorted by date ascending
        """
        results = (
            self.db.query(
                cast(Job.posted_date, Date).label("post_date"),
                func.count(Job.id).label("job_count")
            )
            .filter(Job.posted_date.isnot(None))
            .group_by(cast(Job.posted_date, Date))
            .order_by(cast(Job.posted_date, Date).asc())
            .all()
        )
        return [(row[0], row[1]) for row in results]
    
    def get_recent_jobs(
        self,
        days: int = 30,
        limit: int = 20,
        source_site: Optional[str] = None
    ) -> List[Job]:
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
        
        query = self.db.query(Job).filter(Job.posted_date >= cutoff_date)
        query = self._apply_source_filter(query, source_site)
        
        results = (
            query
            .order_by(Job.posted_date.desc())
            .limit(limit)
            .all()
        )
        return results
    
    def get_salary_distribution(self) -> Dict[str, Optional[float]]:
        """
        Get comprehensive salary distribution statistics.
        
        Returns:
            Dictionary with average_salary, min_salary, max_salary, salary_records
        """
        avg_salary = (Job.salary_min + Job.salary_max) / 2
        
        stats = (
            self.db.query(
                func.avg(avg_salary).label("avg_salary"),
                func.min(avg_salary).label("min_salary"),
                func.max(avg_salary).label("max_salary"),
                func.count(Job.id).label("salary_records")
            )
            .filter(
                Job.salary_min.isnot(None),
                Job.salary_max.isnot(None)
            )
            .first()
        )
        
        if stats and stats.avg_salary is not None:
            return {
                "average_salary": round(float(stats.avg_salary), 2),
                "min_salary": float(stats.min_salary),
                "max_salary": float(stats.max_salary),
                "salary_records": stats.salary_records
            }
        
        return {
            "average_salary": None,
            "min_salary": None,
            "max_salary": None,
            "salary_records": 0
        }
    
    # ============ Sprint 3.3 Methods ============
    
    def get_total_jobs(self) -> int:
        """Get total number of jobs in the database."""
        return self.db.query(Job).count()
    
    def count_recent_jobs(self, days: int = 30) -> int:
        """
        Count jobs posted within the last N days.
        
        This is more efficient than loading ORM objects just to count them.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Count of recent jobs
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        return (
            self.db.query(func.count(Job.id))
            .filter(Job.posted_date >= cutoff_date)
            .scalar()
        )
    
    def count_jobs_by_source_site(self, source_site: str) -> int:
        """
        Count jobs from a specific source site efficiently.
        
        Uses COUNT(*) instead of loading ORM objects.
        
        Args:
            source_site: Source site name
            
        Returns:
            Count of jobs from that source
        """
        return (
            self.db.query(func.count(Job.id))
            .filter(Job.source_site == source_site)
            .scalar()
        )
    
    def get_jobs_with_company_count(self) -> int:
        """Get count of jobs with company name populated."""
        return self.db.query(Job).filter(Job.company_name.isnot(None)).count()
    
    def get_jobs_with_location_count(self) -> int:
        """Get count of jobs with location populated."""
        return self.db.query(Job).filter(Job.location.isnot(None)).count()
    
    def get_jobs_with_salary_count(self) -> int:
        """Get count of jobs with salary data populated."""
        return self.db.query(Job).filter(Job.salary_min.isnot(None)).count()
    
    def get_jobs_with_employment_type_count(self) -> int:
        """Get count of jobs with employment type populated."""
        return self.db.query(Job).filter(Job.employment_type.isnot(None)).count()
    
    def get_jobs_with_posted_date_count(self) -> int:
        """Get count of jobs with posted date populated."""
        return self.db.query(Job).filter(Job.posted_date.isnot(None)).count()
    
    def get_distinct_source_sites(self) -> List[str]:
        """Get distinct source sites in the database."""
        results = self.db.query(Job.source_site).distinct().all()
        return [row[0] for row in results]
    
    def get_skill_relationship_count(self) -> int:
        """Get total number of skill-job relationships."""
        from app.models.job_skill import JobSkill
        return self.db.query(JobSkill).count()
    
    def get_jobs_by_source_site(self, source_site: str) -> List[Job]:
        """Get all jobs from a specific source site."""
        return self.db.query(Job).filter(Job.source_site == source_site).all()