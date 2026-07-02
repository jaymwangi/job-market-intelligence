# app/api/routes/health.py
from fastapi import APIRouter, status
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy")