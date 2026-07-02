# app/api/router.py
from fastapi import APIRouter
from config import settings
from app.api.routes import health_router, jobs_router, analytics_router

api_router = APIRouter(prefix=settings.api_prefix)

api_router.include_router(health_router)
api_router.include_router(jobs_router)
api_router.include_router(analytics_router)