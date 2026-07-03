from typing import Any

from dashboard.api import JOBS, JOB_DETAIL
from dashboard.schemas.jobs import JobListResponse, Job, JobFilters
from dashboard.services.base import BaseService


class JobsService(BaseService):
    """
    Job service with business logic + API normalization.
    
    Inherits from BaseService for consistent API client access.
    """

    def fetch_jobs(self, filters: JobFilters, page: int, page_size: int) -> JobListResponse:
        """Fetch jobs with filters and pagination."""
        # Ensure page is valid
        page = max(1, page)
        page_size = max(1, page_size)
        
        # Build API-compatible params with proper translation
        params = self._build_params(filters, page, page_size)
        
        # Debug: Log to console only (not UI)
        print(f"📤 Fetching jobs with params: {params}")
        
        # Call the API
        raw_response = self.api.get(JOBS, params=params)
        
        # Debug: Log response summary to console only
        print(f"📥 Received {len(raw_response.get('data', []))} jobs, total: {raw_response.get('total', 0)}")
        
        # Normalize API response → Frontend domain model
        return self._normalize_job_list_response(raw_response)

    def fetch_job(self, job_id: str) -> Job:
        """Fetch a single job by ID."""
        endpoint = JOB_DETAIL.format(job_id=job_id)
        raw_data = self.api.get(endpoint)
        return self._normalize_job(raw_data)

    def _build_params(self, filters: JobFilters, page: int, page_size: int) -> dict[str, Any]:
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
        params: dict[str, Any] = {
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

    def _normalize_job(self, raw: dict) -> Job:
        """Normalize a single job from API format to frontend domain model."""
        return Job(
            id=raw["id"],
            title=raw["title"],
            company_name=raw["company_name"],
            location=raw["location"],
            description=raw.get("description"),
            salary_min=raw.get("salary_min"),
            salary_max=raw.get("salary_max"),
            salary_currency=raw.get("salary_currency", "USD"),
            posted_date=raw["posted_date"],
            source_site=raw.get("source_site"),
            source_url=raw.get("source_url"),
            is_active=raw.get("is_active", True),
        )

    def _normalize_job_list_response(self, raw: dict) -> JobListResponse:
        """
        Normalize API response to frontend domain model.
        
        API Response:                    Frontend Domain:
        - page                          - page
        - limit                         - page_size
        - total                         - total
        - data: [...]                   - items: [...]
        """
        items = [self._normalize_job(item) for item in raw.get("data", [])]
        
        total = raw.get("total", len(items))
        limit = raw.get("limit", 20)
        current_page = raw.get("page", 1)
        total_pages = self._calc_total_pages(total, limit)
        
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