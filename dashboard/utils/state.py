# dashboard/utils/state.py
"""Session state management - unified StateManager for Sprint 5.1+ infrastructure."""

import logging
from typing import Any

import streamlit as st

# Use relative imports to avoid circular dependency
from dashboard.api.client import APIClient
from dashboard.core.config import settings
from dashboard.utils.cache import CacheManager

logger = logging.getLogger(__name__)


class StateManager:
    """
    Centralized session state management.
    Unified approach combining ServiceFactory pattern with Streamlit session state.
    """

    # Cache for service instances
    _services: dict[str, Any] = {}
    _api_client: APIClient | None = None
    _cache_manager: CacheManager | None = None

    @classmethod
    def init(cls):
        """Initialize session state with default values."""
        if "initialized" not in st.session_state:
            st.session_state.initialized = True
            st.session_state.current_page = "overview"
            st.session_state.job_filters = {}
            st.session_state.jobs_page = 1
            st.session_state.jobs_page_size = 20
            st.session_state.selected_job_id = None
            st.session_state.services = {}

    @classmethod
    def get_api_client(cls) -> APIClient:
        """Get or create API client singleton."""
        if cls._api_client is None:
            cls._api_client = APIClient(
                base_url=settings.API_BASE_URL, timeout=settings.API_TIMEOUT
            )
        return cls._api_client

    @classmethod
    def get_cache_manager(cls) -> CacheManager:
        """Get or create cache manager singleton."""
        if cls._cache_manager is None:
            cls._cache_manager = CacheManager()
        return cls._cache_manager

    @classmethod
    def get_service(cls, service_class: type) -> Any:
        """
        Get or create a service instance.
        Uses both class-level cache and session state for persistence.
        """
        service_name = service_class.__name__

        # Check class-level cache first
        if service_name in cls._services:
            return cls._services[service_name]

        # Check session state
        if "services" in st.session_state and service_name in st.session_state.services:
            service = st.session_state.services[service_name]
            cls._services[service_name] = service
            return service

        # Create new service instance
        api_client = cls.get_api_client()
        cache_manager = cls.get_cache_manager()
        service = service_class(api_client=api_client, cache_manager=cache_manager)

        # Cache it
        cls._services[service_name] = service
        if "services" not in st.session_state:
            st.session_state.services = {}
        st.session_state.services[service_name] = service

        return service

    @classmethod
    def get_analytics_service(cls):
        """Get analytics service - lazy import to avoid circular dependency."""
        from dashboard.services.analytics_service import AnalyticsService

        return cls.get_service(AnalyticsService)

    @classmethod
    def get_jobs_service(cls):
        """Get jobs service - lazy import to avoid circular dependency."""
        from dashboard.services.jobs_service import JobsService

        return cls.get_service(JobsService)

    @classmethod
    def get_health_service(cls):
        """Get health service - lazy import to avoid circular dependency."""
        from dashboard.services.health import HealthService

        return cls.get_service(HealthService)

    @classmethod
    def clear_cache(cls):
        """Clear all caches."""
        # Clear cache manager
        if cls._cache_manager is not None:
            cls._cache_manager.clear()

        # Clear service caches
        for service in cls._services.values():
            if hasattr(service, "refresh"):
                try:
                    service.refresh()
                except Exception as e:
                    logger.error(f"Error refreshing service: {e}")

        # Clear session state services
        if "services" in st.session_state:
            st.session_state.services = {}

    # ========== Page Navigation Methods ==========

    @classmethod
    def get_current_page(cls) -> str:
        """Get current page from session state."""
        return st.session_state.get("current_page", "overview")

    @classmethod
    def set_current_page(cls, page: str):
        """Set current page in session state."""
        st.session_state.current_page = page

    # ========== Job Filter Methods ==========

    @classmethod
    def get_jobs_filters(cls) -> dict:
        """Get job filters from session state."""
        return st.session_state.get("job_filters", {})

    @classmethod
    def set_jobs_filters(cls, filters: dict):
        """Set job filters in session state."""
        st.session_state.job_filters = filters

    @classmethod
    def reset_jobs_context(cls):
        """Reset jobs context (filters and pagination)."""
        st.session_state.job_filters = {}
        st.session_state.jobs_page = 1
        st.session_state.selected_job_id = None

    # ========== Job Pagination Methods ==========

    @classmethod
    def get_jobs_page(cls) -> int:
        """Get current jobs page number."""
        return st.session_state.get("jobs_page", 1)

    @classmethod
    def set_jobs_page(cls, page: int):
        """Set current jobs page number."""
        st.session_state.jobs_page = max(1, page)

    @classmethod
    def get_jobs_page_size(cls) -> int:
        """Get jobs page size."""
        return st.session_state.get("jobs_page_size", 20)

    @classmethod
    def set_jobs_page_size(cls, page_size: int):
        """Set jobs page size."""
        st.session_state.jobs_page_size = max(1, min(page_size, 100))

    # ========== Backward Compatibility Methods ==========

    @classmethod
    def get_job_filters(cls) -> dict:
        """Alias for get_jobs_filters() for backward compatibility."""
        return cls.get_jobs_filters()

    @classmethod
    def set_job_filters(cls, filters: dict):
        """Alias for set_jobs_filters() for backward compatibility."""
        cls.set_jobs_filters(filters)

    @classmethod
    def get_page(cls) -> int:
        """Alias for get_jobs_page() for backward compatibility."""
        return cls.get_jobs_page()

    @classmethod
    def set_page(cls, page: int):
        """Alias for set_jobs_page() for backward compatibility."""
        cls.set_jobs_page(page)

    # ========== Job Selection Methods ==========

    @classmethod
    def get_selected_job_id(cls) -> str | None:
        """Get selected job ID."""
        return st.session_state.get("selected_job_id", None)

    @classmethod
    def set_selected_job_id(cls, job_id: str | None):
        """Set selected job ID."""
        st.session_state.selected_job_id = job_id

    # ========== Dashboard Methods ==========

    @classmethod
    def refresh_dashboard(cls):
        """Refresh all dashboard data."""
        cls.clear_cache()
        # Reset pagination
        cls.set_jobs_page(1)
        cls.set_selected_job_id(None)


# Convenience functions for backward compatibility
def get_service_factory():
    """
    Factory function for backward compatibility.
    Returns StateManager as a factory-like interface.
    """
    return StateManager


def get_analytics_service():
    """Get analytics service."""
    return StateManager.get_analytics_service()


def get_jobs_service():
    """Get jobs service."""
    return StateManager.get_jobs_service()


def get_health_service():
    """Get health service."""
    return StateManager.get_health_service()


def refresh_dashboard() -> None:
    """Refresh all dashboard data."""
    StateManager.refresh_dashboard()


# For backward compatibility with existing code that expects ServiceFactory
class ServiceFactory:
    """Wrapper class for backward compatibility."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_analytics_service(self):
        return StateManager.get_analytics_service()

    def get_jobs_service(self):
        return StateManager.get_jobs_service()

    def get_health_service(self):
        return StateManager.get_health_service()

    def refresh_all(self) -> None:
        StateManager.clear_cache()
