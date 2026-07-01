"""
Analytics Service Module

This module provides orchestration for analytics queries, combining multiple
repository calls into useful aggregates. The service is intentionally thin
and only contains methods that genuinely add value through orchestration.
"""

from typing import Dict, Any
from app.repositories.analytics_repository import AnalyticsRepository


class AnalyticsService:
    """
    Service layer for analytics operations.
    
    Only contains methods that orchestrate multiple repository calls.
    Simple pass-through methods belong in the repository directly.
    """
    
    def __init__(self, repository: AnalyticsRepository):
        """
        Initialize the service with an analytics repository.
        
        Args:
            repository: AnalyticsRepository instance
        """
        self._repository = repository
    
    def get_dashboard_summary(
        self,
        company_limit: int = 5,
        location_limit: int = 5,
        skill_limit: int = 5,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get a comprehensive dashboard summary combining multiple analytics.
        
        This is the primary orchestration method that brings together
        data from multiple repository queries into a single structure.
        
        Args:
            company_limit: Number of top companies to return
            location_limit: Number of top locations to return
            skill_limit: Number of top skills to return
            days: Number of days for recent jobs count
            
        Returns:
            Dictionary containing all dashboard metrics
        """
        return {
            "total_jobs": self._repository.get_total_jobs(),
            "top_companies": self._repository.get_top_companies(limit=company_limit),
            "top_locations": self._repository.get_jobs_by_location(limit=location_limit),
            "top_skills": self._repository.get_top_skills(limit=skill_limit),
            "salary_statistics": self._repository.get_salary_statistics(),
            "employment_types": self._repository.get_employment_type_distribution(),
            "recent_jobs_count": self._repository.count_recent_jobs(days=days),
            "posting_trend": self._repository.get_jobs_posted_by_date()[-30:],
        }
        
        