# app/api/routes/__init__.py
from .analytics import router as analytics_router
from .health import router as health_router
from .jobs import router as jobs_router

__all__ = ["health_router", "jobs_router", "analytics_router"]
