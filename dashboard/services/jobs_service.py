# dashboard/services/jobs_service.py
"""Job service with business logic + API normalization."""

import logging
from datetime import datetime
from typing import Any

import streamlit as st

from api import JOB_DETAIL, JOBS
from api.client import APIClient
from schemas.jobs import Job, JobFilters, JobListResponse
from services.base import BaseService
from utils.cache import CacheManager

logger = logging.getLogger(__name__)


class JobsService(BaseService):
    """
    Job service with business logic + API normalization.

    Inherits from BaseService for consistent API client access.
    """

    def __init__(self, api_client: APIClient, cache_manager: CacheManager | None = None):
        """Initialize JobsService with API client and cache manager."""
        super().__init__(api_client, cache_manager)

    def fetch_jobs(self, filters: JobFilters, page: int, page_size: int) -> JobListResponse:
        """
        Fetch jobs with filters and pagination.
        Uses cached raw data to avoid pickle serialization issues with Pydantic models.
        """
        page = max(1, page)
        page_size = max(1, page_size)

        # Build params
        params = self._build_params(filters, page, page_size)

        # Get the API base URL from the client
        api_base_url = self.api_client.base_url

        # Fetch cached raw data
        raw_response = self._fetch_jobs_cached(api_base_url, params)

        logger.debug(
            f"Received {len(raw_response.get('data', []))} jobs, total: {raw_response.get('total', 0)}"
        )

        # Normalize to domain model after caching
        return self._normalize_job_list_response(raw_response)

    @staticmethod
    @st.cache_data(ttl=300)
    def _fetch_jobs_cached(api_base_url: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        Static cached method that returns raw dict data.
        This avoids the 'self' hashing issue.
        """
        try:
            # Create a new API client for the cached call
            from api.client import APIClient
            client = APIClient(base_url=api_base_url)
            
            logger.debug(f"Fetching jobs with params (cached): {params}")
            return client.get(JOBS, params=params)
        except Exception as e:
            logger.error(f"Failed to fetch jobs: {e}")
            raise
    def fetch_job(self, job_id: str) -> Job | None:
        """Fetch a single job by ID."""
        try:
            endpoint = JOB_DETAIL.format(job_id=job_id)
            raw_data = self.api_client.get(endpoint)
            return self._normalize_job(raw_data)
        except Exception as e:
            logger.error(f"Failed to fetch job {job_id}: {e}")
            return None

    def _build_params(self, filters: JobFilters, page: int, page_size: int) -> dict[str, Any]:
        """Build API-compatible query parameters."""
        params: dict[str, Any] = {
            "page": page,
            "limit": page_size,
        }

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
        if filters.language:
            params["language"] = filters.language
        if filters.is_tech_role is not None:
            params["is_tech_role"] = filters.is_tech_role

        return params

    def _parse_datetime(self, value: Any) -> datetime:
        """Parse a datetime from various formats."""
        if value is None:
            return datetime.now()

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                try:
                    from dateutil import parser
                    return parser.parse(value)
                except (ValueError, TypeError, ImportError):
                    pass

        logger.warning(f"Could not parse datetime from: {value}, using current time")
        return datetime.now()

    def _normalize_job(self, raw: dict[str, Any]) -> Job:
        """
        Normalize a single job from API format to frontend domain model.
        """
        location = raw.get("location") or ""
        posted_date = self._parse_datetime(raw.get("posted_date"))
        salary_currency = raw.get("salary_currency") or "USD"

        return Job(
            id=str(raw.get("id", "")),
            title=str(raw.get("title", "")),
            company_name=str(raw.get("company_name", "")),
            location=location,
            description=raw.get("description"),
            salary_min=raw.get("salary_min"),
            salary_max=raw.get("salary_max"),
            salary_currency=salary_currency,
            posted_date=posted_date,
            source_site=raw.get("source_site"),
            source_url=raw.get("source_url"),
            is_active=bool(raw.get("is_active", True)),
            language=raw.get("language", "en"),
            skills=raw.get("skills", []),
            technology_category=raw.get("technology_category"),
            is_tech_role=raw.get("is_tech_role", False),
            country_code=raw.get("country_code"),
            currency=raw.get("currency"),
            employment_type=raw.get("employment_type"),
        )

    def _normalize_job_list_response(self, raw: dict[str, Any]) -> JobListResponse:
        """Normalize API response to frontend domain model."""
        items: list[Job] = [self._normalize_job(item) for item in raw.get("data", [])]

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
        st.cache_data.clear()
        logger.info("JobsService cache cleared")