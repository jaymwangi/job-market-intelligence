# app/api/router.py
from fastapi import APIRouter

from app.api.routes.analytics import router as analytics_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from config.settings import settings

api_router = APIRouter(prefix=settings.api_prefix)

api_router.include_router(health_router)
api_router.include_router(jobs_router)
api_router.include_router(analytics_router)
