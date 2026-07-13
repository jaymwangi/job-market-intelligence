# app/api/router.py
from fastapi import APIRouter

from app.api.routes.analytics import router as analytics_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router

# Remove the prefix here - it will be added in main.py
api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(jobs_router)
api_router.include_router(analytics_router)
