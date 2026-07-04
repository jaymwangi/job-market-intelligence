# dashboard/utils/service_factory.py
"""Service factory - delegates to StateManager for consistency."""
from dashboard.services.jobs_service import JobsService
from dashboard.services.analytics_service import AnalyticsService
from dashboard.services.health import HealthService
from dashboard.utils.state import StateManager


def get_jobs_service() -> JobsService:
    """Get jobs service from StateManager."""
    return StateManager.get_jobs_service()


def get_analytics_service() -> AnalyticsService:
    """Get analytics service from StateManager."""
    return StateManager.get_analytics_service()


def get_health_service() -> HealthService:
    """Get health service from StateManager."""
    return StateManager.get_health_service()


def clear_service_cache() -> None:
    """Clear all service caches."""
    StateManager.clear_cache()