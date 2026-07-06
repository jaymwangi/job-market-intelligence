# dashboard/utils/__init__.py
"""Utils package."""
from .state import StateManager
from .cache import CacheManager, cached

# Lazy imports for service factory to avoid circular imports
def get_service_factory():
    """Get service factory."""
    from .service_factory import get_jobs_service, get_analytics_service, get_health_service
    return {
        "get_jobs_service": get_jobs_service,
        "get_analytics_service": get_analytics_service,
        "get_health_service": get_health_service,
    }

__all__ = [
    "StateManager",
    "CacheManager",
    "cached",
    "get_service_factory",
]