"""
Analytics Repository Module

This module provides read-only aggregation queries for job market analytics.
All queries are optimized to run directly on PostgreSQL against the actual
project schema where company_name, location, and employment_type are stored
directly on the Job table.
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
        """
        Initialize the repository with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
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
    
    def get_top_companies(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get companies with the most job postings.
        
        Since company_name is stored directly on the Job table,
        we query it directly without a separate Company table.
        
        Args:
            limit: Maximum number of companies to return
            
        Returns:
            List of tuples (company_name, job_count)
        """
        results = (
            self.db.query(
                Job.company_name,
                func.count(Job.id)
            )
            .filter(Job.company_name.isnot(None))
            .group_by(Job.company_name)
            .order_by(func.count(Job.id).desc())
            .limit(limit)
            .all()
        )
        
        return [(row[0], row[1]) for row in results]
    
    def get_jobs_by_location(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get job distribution by location.
        
        Since location is stored directly on the Job table,
        we query it directly without a separate Location table.
        
        Args:
            limit: Maximum number of locations to return
            
        Returns:
            List of tuples (location, job_count)
        """
        results = (
            self.db.query(
                Job.location,
                func.count(Job.id)
            )
            .filter(Job.location.isnot(None))
            .group_by(Job.location)
            .order_by(func.count(Job.id).desc())
            .limit(limit)
            .all()
        )
        
        return [(row[0], row[1]) for row in results]
    
    def get_salary_statistics(self) -> Dict[str, Optional[float]]:
        """
        Compute salary statistics from job postings with salary data.
        
        Each statistic is calculated independently, ignoring only its own
        NULL values to maximize data retention.
        
        Returns:
            Dictionary with keys: avg_min, avg_max, min_salary, max_salary
            Values are floats rounded to 2 decimal places.
            If no salary data exists, all values are None.
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
        
        Since employment_type is stored directly on the Job table,
        we query it directly without a separate EmploymentType table.
        
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
    
    def get_salary_by_location(self, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Calculate average salary grouped by location.
        
        Uses the average of salary_min and salary_max for each job,
        then averages across jobs in each location.
        
        Args:
            limit: Maximum number of locations to return
            
        Returns:
            List of tuples (location, average_salary)
        """
        # Define salary expression once for reuse
        avg_salary_expr = (Job.salary_min + Job.salary_max) / 2
        
        results = (
            self.db.query(
                Job.location,
                func.avg(avg_salary_expr).label("avg_salary")
            )
            .filter(
                Job.location.isnot(None),
                Job.salary_min.isnot(None),
                Job.salary_max.isnot(None)
            )
            .group_by(Job.location)
            .order_by(func.avg(avg_salary_expr).desc())
            .limit(limit)
            .all()
        )
        
        return [(row[0], float(row[1])) for row in results]
    
    def get_salary_by_company(self, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Calculate average salary grouped by company.
        
        Uses the average of salary_min and salary_max for each job,
        then averages across jobs for each company.
        
        Args:
            limit: Maximum number of companies to return
            
        Returns:
            List of tuples (company_name, average_salary)
        """
        # Define salary expression once for reuse
        avg_salary_expr = (Job.salary_min + Job.salary_max) / 2
        
        results = (
            self.db.query(
                Job.company_name,
                func.avg(avg_salary_expr).label("avg_salary")
            )
            .filter(
                Job.company_name.isnot(None),
                Job.salary_min.isnot(None),
                Job.salary_max.isnot(None)
            )
            .group_by(Job.company_name)
            .order_by(func.avg(avg_salary_expr).desc())
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
        # Use SQLAlchemy's Date type for casting
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
        limit: int = 20
    ) -> List[Job]:
        """
        Retrieve jobs posted within the last N days.
        
        Returns ORM Job objects, not dictionaries. This allows callers
        to access all Job attributes and relationships as needed.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of jobs to return
            
        Returns:
            List of Job ORM models
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        results = (
            self.db.query(Job)
            .filter(Job.posted_date >= cutoff_date)
            .order_by(Job.posted_date.desc())
            .limit(limit)
            .all()
        )
        
        return results
    
    def get_salary_distribution(self) -> Dict[str, Optional[float]]:
        """
        Get comprehensive salary distribution statistics.
        
        Returns:
            Dictionary with keys:
                - average_salary: Average of all job salaries
                - min_salary: Minimum salary
                - max_salary: Maximum salary
                - salary_records: Count of jobs with salary data
        """
        # Define salary expression once for reuse
        avg_salary_expr = (Job.salary_min + Job.salary_max) / 2
        
        stats = (
            self.db.query(
                func.avg(avg_salary_expr).label("avg_salary"),
                func.min(avg_salary_expr).label("min_salary"),
                func.max(avg_salary_expr).label("max_salary"),
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