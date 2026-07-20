"""Job listing extractor."""

from typing import Any, Dict, List, Optional
import logging
from app.etl.clients.http_client import HTTPClient

logger = logging.getLogger(__name__)

# Constants
RAW_SOURCE_COUNTRY_FIELD = "_source_country"

# Type aliases
RawJob = Dict[str, Any]
RawJobs = List[RawJob]


def mask_sensitive(value: str, show: int = 4) -> str:
    """Mask sensitive strings, showing only first few characters."""
    if not value:
        return "None"
    if len(value) <= show:
        return "*" * len(value)
    return f"{value[:show]}..."


def mask_params(params: dict[str, Any] | None) -> dict[str, str]:
    """Mask sensitive parameters for logging."""
    if not params:
        return {}

    masked = {}
    sensitive_keys = {"app_id", "app_key", "api_key", "key", "id", "secret", "password", "token"}

    for key, value in params.items():
        if key.lower() in sensitive_keys or any(s in key.lower() for s in sensitive_keys):
            masked[key] = mask_sensitive(str(value))
        else:
            masked[key] = str(value)

    return masked


class JobsExtractor:
    """Fetches job listings from external API."""

    def __init__(
        self,
        api_url: str,
        app_id: str,
        api_key: str,
        debug: bool = False,
        results_per_page: int = 25,
        max_pages: int = 5,
        client: Optional[HTTPClient] = None,
    ):
        """
        Initialize the job extractor.

        Args:
            api_url: Base API URL
            app_id: Adzuna app ID
            api_key: Adzuna app key
            debug: Enable debug logging
            results_per_page: Number of results per page
            max_pages: Maximum number of pages to fetch
            client: Optional HTTP client (for testing)
        """
        self.api_url = api_url
        self.app_id = app_id
        self.api_key = api_key
        self.debug = debug
        self.results_per_page = results_per_page
        self.max_pages = max_pages
        self.client = client or HTTPClient(debug=debug)

    def extract(self, country: str = "gb") -> RawJobs:
        """
        Extract jobs from API for a specific country.

        Args:
            country: Country code (gb, us, de, etc.)

        Returns:
            List of raw job dictionaries with source-country metadata attached.
        """
        if not self.app_id or not self.api_key:
            logger.warning("API credentials not configured")
            return []

        all_jobs: RawJobs = []

        try:
            for page in range(1, self.max_pages + 1):
                jobs, has_more = self._fetch_page(country, page)

                # Add source country to each job for later normalization
                for job in jobs:
                    job[RAW_SOURCE_COUNTRY_FIELD] = country

                all_jobs.extend(jobs)

                if not has_more or len(jobs) < self.results_per_page:
                    break

        except Exception:
            logger.exception(
                "Unexpected error fetching jobs for %s",
                country,
            )

        logger.info(
            "Extracted %d jobs from %s",
            len(all_jobs),
            country,
        )
        return all_jobs

    def _fetch_page(self, country: str, page: int) -> tuple[RawJobs, bool]:
        """
        Fetch a single page of results.

        Args:
            country: Country code
            page: Page number

        Returns:
            Tuple of (jobs_list, has_more_pages)
        """
        params = {
            "app_id": self.app_id,
            "app_key": self.api_key,
            "results_per_page": self.results_per_page,
        }

        url = f"{self.api_url}/jobs/{country}/search/{page}"

        if self.debug:
            logger.debug("📍 URL: %s", url)
            logger.debug("📦 Params: %s", mask_params(params))

        response = self.client.get(url, params=params)

        # Validate response shape
        if not isinstance(response, dict):
            logger.error(
                "Unexpected API response type: %s",
                type(response).__name__,
            )
            return [], False

        jobs = response.get("results", [])
        if not isinstance(jobs, list):
            logger.error("Unexpected 'results' type: %s", type(jobs).__name__)
            return [], False

        total_results = response.get("count", 0)
        if not isinstance(total_results, int):
            total_results = 0

        has_more = total_results > page * self.results_per_page

        return jobs, has_more