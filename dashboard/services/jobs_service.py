# dashboard/services/jobs_service.py
"""Job service with business logic + API normalization."""
from typing import Any, Optional, Dict, List
import logging
from datetime import datetime

from dashboard.api import JOBS, JOB_DETAIL
from dashboard.schemas.jobs import JobListResponse, Job, JobFilters
from dashboard.services.base import BaseService
from dashboard.api.client import APIClient
from dashboard.utils.cache import CacheManager

logger = logging.getLogger(__name__)


class JobsService(BaseService):
    """
    Job service with business logic + API normalization.
    
    Inherits from BaseService for consistent API client access.
    """

    def __init__(self, api_client: APIClient, cache_manager: Optional[CacheManager] = None):
        """Initialize JobsService with API client and cache manager."""
        super().__init__(api_client, cache_manager)

    def fetch_jobs(self, filters: JobFilters, page: int, page_size: int) -> JobListResponse:
        """Fetch jobs with filters and pagination."""
        # Ensure page is valid
        page = max(1, page)
        page_size = max(1, page_size)
        
        # Build API-compatible params with proper translation
        params = self._build_params(filters, page, page_size)
        
        # Debug: Log to console only (not UI)
        logger.debug(f"Fetching jobs with params: {params}")
        
        # Call the API - using self.api_client (from BaseService)
        raw_response = self.api_client.get(JOBS, params=params)
        
        # Debug: Log response summary to console only
        logger.debug(f"Received {len(raw_response.get('data', []))} jobs, total: {raw_response.get('total', 0)}")
        
        # Normalize API response → Frontend domain model
        return self._normalize_job_list_response(raw_response)

    def fetch_job(self, job_id: str) -> Optional[Job]:
        """Fetch a single job by ID."""
        try:
            endpoint = JOB_DETAIL.format(job_id=job_id)
            raw_data = self.api_client.get(endpoint)
            return self._normalize_job(raw_data)
        except Exception as e:
            logger.error(f"Failed to fetch job {job_id}: {e}")
            return None

    def _build_params(self, filters: JobFilters, page: int, page_size: int) -> Dict[str, Any]:
        """
        Build API-compatible query parameters.
        
        CRITICAL: Map frontend field names → API parameter names:
        - search → q (API uses 'q' for search)
        - company → company_name (API uses 'company_name')
        - min_salary → min_salary (API uses 'min_salary')
        - max_salary → max_salary (API uses 'max_salary')
        - page_size → limit (API uses 'limit')
        
        Only include parameters that have valid, non-empty values.
        """
        params: Dict[str, Any] = {
            "page": page,
            "limit": page_size,
        }
        
        # Add filters only if they have valid values
        if filters.search and filters.search.strip():
            params["q"] = filters.search.strip()
        if filters.company and filters.company.strip():
            params["company_name"] = filters.company.strip()
        if filters.location and filters.location.strip():
            params["location"] = filters.location.strip()
        if filters.source_site and filters.source_site.strip():
            params["source_site"] = filters.source_site.strip()
        if filters.min_salary is not None and filters.min_salary > 0:
            params["min_salary"] = filters.min_salary
        if filters.max_salary is not None and filters.max_salary > 0:
            params["max_salary"] = filters.max_salary
        
        return params

    def _parse_datetime(self, value: Any) -> datetime:
        """
        Parse a datetime from various formats.
        Returns current datetime if parsing fails.
        """
        if value is None:
            return datetime.now()
        
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            try:
                # Try ISO format first
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                try:
                    # Try dateutil parser as fallback
                    from dateutil import parser
                    return parser.parse(value)
                except (ValueError, TypeError, ImportError):
                    pass
        
        # Fallback to current datetime
        logger.warning(f"Could not parse datetime from: {value}, using current time")
        return datetime.now()

    def _normalize_job(self, raw: Dict[str, Any]) -> Job:
        """
        Normalize a single job from API format to frontend domain model.
        
        Handles None values for required fields by providing defaults.
        """
        # Handle location - if None, use empty string
        location = raw.get("location")
        if location is None:
            location = ""
        
        # Handle posted_date - parse to datetime
        posted_date = self._parse_datetime(raw.get("posted_date"))
        
        # Handle salary_currency - if None, use "USD"
        salary_currency = raw.get("salary_currency")
        if salary_currency is None:
            salary_currency = "USD"
        
        # Build the job with proper type handling
        return Job(
            id=str(raw.get("id", "")),
            title=str(raw.get("title", "")),
            company_name=str(raw.get("company_name", "")),
            location=location,  # Ensure it's a string, not None
            description=raw.get("description"),
            salary_min=raw.get("salary_min"),
            salary_max=raw.get("salary_max"),
            salary_currency=salary_currency,  # Ensure it's a string, not None
            posted_date=posted_date,  # Now it's a datetime object
            source_site=raw.get("source_site"),
            source_url=raw.get("source_url"),
            is_active=bool(raw.get("is_active", True)),
        )

    def _normalize_job_list_response(self, raw: Dict[str, Any]) -> JobListResponse:
        """
        Normalize API response to frontend domain model.
        
        API Response:                    Frontend Domain:
        - page                          - page
        - limit                         - page_size
        - total                         - total
        - data: [...]                   - items: [...]
        """
        items: List[Job] = [self._normalize_job(item) for item in raw.get("data", [])]
        
        total: int = raw.get("total", len(items))
        limit: int = raw.get("limit", 20)
        current_page: int = raw.get("page", 1)
        total_pages: int = self._calc_total_pages(total, limit)
        
        return JobListResponse(
            items=items,
            total=total,
            page=current_page,
            page_size=limit,
            total_pages=total_pages,
        )

    def _calc_total_pages(self, total: int, limit: int) -> int:
        """Calculate total pages safely."""
        if limit <= 0:
            return 1
        return max(1, (total + limit - 1) // limit)

    def refresh(self) -> None:
        """Refresh job service cache."""
        super().refresh()
        logger.info("JobsService cache cleared")