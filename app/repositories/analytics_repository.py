"""
Analytics Repository Module

This module provides read-only aggregation queries for job market analytics.
All queries are optimized to run directly on PostgreSQL against the actual
project schema where company_name, location, and employment_type are stored
directly on the Job table.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.job import Job
from app.models.skill import Skill
from app.models.job_skill import JobSkill


class AnalyticsRepository:
    """
    Repository for analytics queries on job market data.
    
    All methods are read-only and return raw query results.
    No business logic, formatting, or presentation concerns.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
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
        # Calculate each statistic independently
        stats = self.db.query(
            func.avg(Job.salary_min).label("avg_min"),
            func.avg(Job.salary_max).label("avg_max"),
            func.min(Job.salary_min).label("min_salary"),
            func.max(Job.salary_max).label("max_salary")
        ).first()
        
        # Check if we have any data
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