"""Pure HTTP transport layer."""

import logging
from types import TracebackType
from typing import Any, Optional

import httpx

from .exceptions import (
    APIConnectionError,
    APIError,
    APINotFoundError,
    APIServerError,
    APITimeoutError,
)

logger = logging.getLogger(__name__)


class APIClient:
    """Pure HTTP client for backend API communication."""

    def __init__(self, base_url: str, timeout: int = 30, retries: int = 3):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the backend API
            timeout: Request timeout in seconds
            retries: Number of retry attempts for failed requests
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (can include query params)
            params: Query parameters (for GET requests)
            data: Form data
            json: JSON payload

        Returns:
            Response data as dictionary

        Raises:
            APITimeoutError: If request times out
            APIConnectionError: If connection fails
            APINotFoundError: If resource not found (404)
            APIServerError: If server error (5xx)
            APIError: For other API errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        logger.debug("API Request: %s %s", method, url)
        if params:
            logger.debug("Params: %s", params)
        if json:
            logger.debug("JSON: %s", json)

        for attempt in range(self.retries):
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                result = response.json()
                logger.debug("Status: %s", response.status_code)
                return result

            except httpx.TimeoutException as e:
                logger.warning(
                    "Timeout on attempt %d/%d: %s",
                    attempt + 1,
                    self.retries,
                    url,
                )
                if attempt == self.retries - 1:
                    raise APITimeoutError("Request timed out") from e
                continue

            except httpx.ConnectError as e:
                logger.warning(
                    "Connection error on attempt %d/%d: %s",
                    attempt + 1,
                    self.retries,
                    url,
                )
                if attempt == self.retries - 1:
                    raise APIConnectionError("Failed to connect to API") from e
                continue

            except httpx.HTTPStatusError as e:
                detail = e.response.text
                try:
                    error_data = e.response.json()
                    if "detail" in error_data:
                        detail = str(error_data["detail"])
                except ValueError:
                    pass

                logger.error("HTTP error %d: %s", e.response.status_code, detail)

                if e.response.status_code == 404:
                    raise APINotFoundError(f"Resource not found: {detail}") from e
                elif e.response.status_code == 422:
                    raise APIError(f"Validation error: {detail}") from e
                elif e.response.status_code >= 500:
                    raise APIServerError(f"Server error: {detail}") from e
                raise APIError(f"Request failed: {e.response.status_code} - {detail}") from e

            except Exception as e:
                logger.exception("Unexpected error during API request")
                raise APIError(f"Unexpected error: {e}") from e

        raise APIError("Request failed after all retries")

    # ============================================================
    # HTTP Methods
    # ============================================================

    def get(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Perform GET request with query parameters."""
        return self._make_request("GET", endpoint, params=params)

    def post(
        self,
        endpoint: str,
        json: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Perform POST request.
        
        Note: For query parameters, include them in the endpoint URL.
        """
        return self._make_request("POST", endpoint, json=json, data=data)

    def put(
        self,
        endpoint: str,
        json: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Perform PUT request.
        
        Note: For query parameters, include them in the endpoint URL.
        """
        return self._make_request("PUT", endpoint, json=json, data=data)

    def delete(
        self,
        endpoint: str,
    ) -> dict[str, Any]:
        """Perform DELETE request."""
        return self._make_request("DELETE", endpoint)

    def patch(
        self,
        endpoint: str,
        json: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Perform PATCH request.
        
        Note: For query parameters, include them in the endpoint URL.
        """
        return self._make_request("PATCH", endpoint, json=json, data=data)

    # ============================================================
    # Health Methods
    # ============================================================

    def health(self) -> dict[str, Any]:
        """Check API health."""
        return self.get("api/v1/health")

    def live(self) -> dict[str, Any]:
        """Check liveness."""
        return self.get("api/v1/health/live")

    def ready(self) -> dict[str, Any]:
        """Check readiness."""
        return self.get("api/v1/health/ready")

    # ============================================================
    # Job Methods
    # ============================================================

    def get_jobs(
        self,
        page: int = 1,
        limit: int = 20,
        q: Optional[str] = None,
        company_name: Optional[str] = None,
        location: Optional[str] = None,
        source_site: Optional[str] = None,
        min_salary: Optional[float] = None,
        max_salary: Optional[float] = None,
        country_code: Optional[str] = None,
        technology_category: Optional[str] = None,
        employment_type: Optional[str] = None,
        is_tech_role: Optional[bool] = None,
        language: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get paginated list of jobs with filters.

        Args:
            page: Page number
            limit: Items per page
            q: Search query
            company_name: Filter by company
            location: Filter by location
            source_site: Filter by source site
            min_salary: Minimum salary
            max_salary: Maximum salary
            country_code: Filter by country code
            technology_category: Filter by tech category
            employment_type: Filter by employment type
            is_tech_role: Filter to tech roles
            language: Filter by language

        Returns:
            Paginated job list response
        """
        params: dict[str, Any] = {"page": page, "limit": limit}
        if q:
            params["q"] = q
        if company_name:
            params["company_name"] = company_name
        if location:
            params["location"] = location
        if source_site:
            params["source_site"] = source_site
        if min_salary is not None:
            params["min_salary"] = min_salary
        if max_salary is not None:
            params["max_salary"] = max_salary
        if country_code:
            params["country_code"] = country_code
        if technology_category:
            params["technology_category"] = technology_category
        if employment_type:
            params["employment_type"] = employment_type
        if is_tech_role is not None:
            params["is_tech_role"] = str(is_tech_role).lower()
        if language:
            params["language"] = language

        return self.get("api/v1/jobs", params=params)

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Get a single job by ID."""
        return self.get(f"api/v1/jobs/{job_id}")

    # ============================================================
    # Sprint 6.6: Translation Method
    # ============================================================

    def translate_job(
        self,
        job_id: str,
        target_language: str = "en",
    ) -> dict[str, Any]:
        """
        Translate a job posting.

        Args:
            job_id: Job UUID
            target_language: Target language code (default: 'en')

        Returns:
            Translation result with original and translated text
        """
        # POST with query params in URL
        url = f"api/v1/jobs/{job_id}/translate?target_language={target_language}"
        return self.post(url)

    # ============================================================
    # Analytics Methods - Top Lists
    # ============================================================

    def get_top_skills(self, limit: int = 10) -> dict[str, Any]:
        """Get top skills."""
        return self.get("api/v1/analytics/top-skills", params={"limit": limit})

    def get_top_companies(self, limit: int = 10) -> dict[str, Any]:
        """Get top companies."""
        return self.get("api/v1/analytics/top-companies", params={"limit": limit})

    def get_jobs_by_location(self, limit: int = 10) -> dict[str, Any]:
        """Get jobs by location."""
        return self.get("api/v1/analytics/jobs-by-location", params={"limit": limit})

    # ============================================================
    # Analytics Methods - Salary
    # ============================================================

    def get_salary_statistics(self) -> dict[str, Any]:
        """Get salary statistics."""
        return self.get("api/v1/analytics/salary-statistics")

    def get_salary_by_location(self, limit: int = 10) -> dict[str, Any]:
        """Get salary by location."""
        return self.get("api/v1/analytics/salary-by-location", params={"limit": limit})

    def get_salary_by_company(self, limit: int = 10) -> dict[str, Any]:
        """Get salary by company."""
        return self.get("api/v1/analytics/salary-by-company", params={"limit": limit})

    def get_salary_distribution(self) -> dict[str, Any]:
        """Get salary distribution."""
        return self.get("api/v1/analytics/salary-distribution")

    # ============================================================
    # Analytics Methods - Trends & Distribution
    # ============================================================

    def get_employment_types(self) -> dict[str, Any]:
        """Get employment type distribution."""
        return self.get("api/v1/analytics/employment-types")

    def get_posting_trend(self, days: int = 30) -> dict[str, Any]:
        """Get posting trend."""
        return self.get("api/v1/analytics/posting-trend", params={"days": days})

    def get_recent_jobs(self, days: int = 7) -> dict[str, Any]:
        """Get recent jobs count."""
        return self.get("api/v1/analytics/recent-jobs", params={"days": days})

    # ============================================================
    # Analytics Methods - Summaries
    # ============================================================

    def get_dataset_summary(self) -> dict[str, Any]:
        """Get dataset summary."""
        return self.get("api/v1/analytics/dataset-summary")

    def get_overview(self) -> dict[str, Any]:
        """Get overview."""
        return self.get("api/v1/analytics/overview")

    def get_dashboard_summary(self) -> dict[str, Any]:
        """Get dashboard summary."""
        return self.get("api/v1/analytics/dashboard-summary")

    # ============================================================
    # Sprint 6.6: Language Analytics
    # ============================================================

    def get_language_distribution(self) -> dict[str, Any]:
        """Get job distribution by language."""
        return self.get("api/v1/analytics/language/distribution")

    def get_language_by_country(self) -> dict[str, Any]:
        """Get language distribution by country."""
        return self.get("api/v1/analytics/language/by-country")

    def get_english_vs_non_english(self) -> dict[str, Any]:
        """Get English vs non-English distribution."""
        return self.get("api/v1/analytics/language/english-vs-non-english")

    def get_language_salary_stats(self) -> dict[str, Any]:
        """Get salary by language."""
        return self.get("api/v1/analytics/language/salary")

    # ============================================================
    # Sprint 6.6: Technology Analytics
    # ============================================================

    def get_tech_vs_non_tech(self) -> dict[str, Any]:
        """Get tech vs non-tech distribution."""
        return self.get("api/v1/analytics/tech/vs-non-tech")

    def get_tech_category_distribution(self) -> dict[str, Any]:
        """Get technology category distribution."""
        return self.get("api/v1/analytics/tech/category-distribution")

    def get_tech_by_country(self) -> dict[str, Any]:
        """Get tech roles by country."""
        return self.get("api/v1/analytics/tech/by-country")

    def get_tech_skills(self, limit: int = 20) -> dict[str, Any]:
        """Get skills in tech roles."""
        return self.get("api/v1/analytics/tech/skills", params={"limit": limit})

    def get_tech_salary_stats(self) -> dict[str, Any]:
        """Get salary statistics for tech roles."""
        return self.get("api/v1/analytics/tech/salary")

    # ============================================================
    # Sprint 6.6: Enriched Combined Analytics
    # ============================================================

    def get_enriched_skills(
        self,
        limit: int = 20,
        country_code: Optional[str] = None,
        tech_only: bool = False,
    ) -> dict[str, Any]:
        """Get enriched skills with filters."""
        params: dict[str, Any] = {"limit": limit}
        if country_code:
            params["country_code"] = country_code
        if tech_only:
            params["tech_only"] = "true"
        return self.get("api/v1/analytics/enriched/skills", params=params)

    def get_enriched_countries(self) -> dict[str, Any]:
        """Get country distribution."""
        return self.get("api/v1/analytics/enriched/countries")

    def get_enriched_technology(self) -> dict[str, Any]:
        """Get technology distribution."""
        return self.get("api/v1/analytics/enriched/technology")

    def get_enriched_salary(
        self,
        country_code: Optional[str] = None,
        tech_only: bool = False,
    ) -> dict[str, Any]:
        """Get enriched salary statistics with filters."""
        params: dict[str, Any] = {}
        if country_code:
            params["country_code"] = country_code
        if tech_only:
            params["tech_only"] = "true"
        return self.get("api/v1/analytics/enriched/salary", params=params)

    # ============================================================
    # Lifecycle
    # ============================================================

    def close(self) -> None:
        """Close the client session."""
        self.client.close()

    def __enter__(self) -> "APIClient":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Exit context manager and close client."""
        self.close()