# app/api/routes/health.py
from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from config import settings, get_logger
from app.database.session import get_db
from app.schemas.common import HealthResponse

logger = get_logger("app.api.routes.health")
router = APIRouter(tags=["Health"])


def check_database_connection(db: Session) -> bool:
    """Check if database connection is working."""
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check API health including database connectivity."
)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    db_healthy = check_database_connection(db)
    
    status_text = "healthy" if db_healthy else "degraded"
    db_status = "connected" if db_healthy else "disconnected"
    
    logger.info(f"Health check: {status_text}, database: {db_status}")
    
    return HealthResponse(
        status=status_text,
        database=db_status,
        environment=settings.environment,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )