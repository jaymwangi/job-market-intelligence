# dashboard/utils/state.py
"""Session state management - unified StateManager for Sprint 5.1+ infrastructure."""

import logging
from typing import Any, Dict, Optional
from datetime import datetime

import streamlit as st

# Use relative imports to avoid circular dependency
from dashboard.api.client import APIClient
from core.config import settings
from utils.cache import CacheManager

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
    _etl_status_cache: Optional[Dict] = None
    _etl_cache_timestamp: Optional[datetime] = None

    @classmethod
    def init(cls):
        """Initialize session state with default values."""
        if "initialized" not in st.session_state:
            st.session_state.initialized = True
            st.session_state.current_page = "overview"
            st.session_state.job_filters = {}
            st.session_state.jobs_page = 1
            st.session_state.jobs_page_size = 10
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
        from services.analytics_service import AnalyticsService

        return cls.get_service(AnalyticsService)

    @classmethod
    def get_jobs_service(cls):
        """Get jobs service - lazy import to avoid circular dependency."""
        from services.jobs_service import JobsService

        return cls.get_service(JobsService)

    @classmethod
    def get_health_service(cls):
        """Get health service - lazy import to avoid circular dependency."""
        from services.health import HealthService

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
        
        # Clear ETL status cache
        cls._etl_status_cache = None
        cls._etl_cache_timestamp = None

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

    # ========== ETL Status Methods ==========

    @classmethod
    @st.cache_data(ttl=60)  # Cache for 60 seconds
    def get_etl_status(cls) -> Dict[str, Any]:
        """
        Get ETL pipeline status with caching.
        Returns dict with status, last_run, etc.
        """
        try:
            # Try to get from API first
            api_client = cls.get_api_client()
            response = api_client.get("/analytics/etl/status")
            if response:
                return response
        except Exception as e:
            logger.warning(f"API unavailable for ETL status, using fallback: {e}")

        # Fallback: use analytics service directly
        try:
            analytics_service = cls.get_analytics_service()
            return {
                'status': analytics_service.get_pipeline_status(),
                'last_run': analytics_service.get_last_etl_run(),
                'last_run_time': analytics_service.get_last_etl_run_time(),
                'db_status': analytics_service.get_db_status(),
            }
        except Exception as e:
            logger.error(f"Failed to get ETL status: {e}")
            return {
                'status': 'unknown',
                'last_run': 'N/A',
                'error': str(e)
            }

    @classmethod
    def get_last_etl_run(cls) -> str:
        """Get formatted last ETL run time."""
        status = cls.get_etl_status()
        return status.get('last_run', 'No runs yet')

    @classmethod
    def get_pipeline_status(cls) -> str:
        """Get current pipeline status (Running/Idle)."""
        status = cls.get_etl_status()
        return status.get('status', 'Unknown')

    @classmethod
    def get_db_status(cls) -> str:
        """Get database status."""
        status = cls.get_etl_status()
        return status.get('db_status', 'Unknown')

    @classmethod
    def refresh_etl_status(cls):
        """Force refresh ETL status cache."""
        cls._etl_status_cache = None
        cls._etl_cache_timestamp = None
        st.cache_data.clear()

    # ========== Dashboard Methods ==========

    @classmethod
    def refresh_dashboard(cls):
        """Refresh all dashboard data."""
        cls.clear_cache()
        cls.refresh_etl_status()
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


def get_etl_status():
    """Get ETL status - convenience function."""
    return StateManager.get_etl_status()


def get_last_etl_run():
    """Get formatted last ETL run - convenience function."""
    return StateManager.get_last_etl_run()


def get_pipeline_status():
    """Get pipeline status - convenience function."""
    return StateManager.get_pipeline_status()


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
    
    def get_etl_status(self):
        """Get ETL status."""
        return StateManager.get_etl_status()
    
    def get_last_etl_run(self):
        """Get formatted last ETL run."""
        return StateManager.get_last_etl_run()
    
    def get_pipeline_status(self):
        """Get pipeline status."""
        return StateManager.get_pipeline_status()