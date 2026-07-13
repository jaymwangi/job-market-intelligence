from datetime import datetime, UTC
import time
import logging
from typing import Dict, Any, Tuple

from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.health import check_database_connection as check_db_health
from app.schemas.common import HealthResponse
from config import settings

# Import metrics collector
try:
    from app.core.metrics import metrics_collector
except ImportError:
    class DummyMetricsCollector:
        def get_metrics(self) -> Dict[str, Any]:
            return {"error": "Metrics collector not available"}
    metrics_collector = DummyMetricsCollector()  # type: ignore

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)

# Application start time for uptime tracking
APP_START_TIME: float = time.perf_counter()


def check_database_connection_with_timing(db: Session, log: logging.Logger) -> Tuple[bool, float]:
    """
    Check if database connection is working and measure response time.
    
    Args:
        db: Database session
        log: Request-scoped logger
    
    Returns:
        Tuple of (is_healthy, response_time_ms)
    """
    try:
        start_time = time.perf_counter()
        # Call the database health check with db and log
        is_healthy = check_db_health(db, log)
        response_time = (time.perf_counter() - start_time) * 1000
        return is_healthy, response_time
    except Exception as exc:
        # log.exception already includes the exception info
        log.exception(
            f"Database health check failed: {type(exc).__name__}"
        )
        return False, 0.0


# ============================================================================
# Liveness - Process is running
# ============================================================================

@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Returns 200 OK if the application process is running.",
    include_in_schema=False,
)
async def liveness() -> Dict[str, str]:
    """
    Liveness probe for infrastructure (Render, Kubernetes, etc.).
    
    This endpoint NEVER checks the database or any external dependencies.
    It only confirms the Python process is alive and FastAPI is running.
    
    Returns:
        Simple status indicating the process is alive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(UTC).isoformat()
    }


# ============================================================================
# Readiness - Application is ready to serve traffic
# ============================================================================

@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Returns 200 OK if the application is ready to serve traffic.",
    include_in_schema=False,
)
async def readiness(
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Readiness probe for infrastructure.
    
    Checks that the application is ready to serve traffic by verifying:
    - Database connectivity
    
    Returns 503 Service Unavailable if dependencies are unhealthy.
    """
    log = request.state.logger
    
    db_healthy, db_response_ms = check_database_connection_with_timing(db, log)
    
    if not db_healthy:
        log.warning(
            f"Readiness check failed - database unavailable (response time: {round(db_response_ms, 2)}ms)",
            extra={
                "environment": settings.environment,
            }
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "reason": "Database unavailable",
                "environment": settings.environment,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
    
    return {
        "status": "ready",
        "environment": settings.environment,
        "timestamp": datetime.now(UTC).isoformat()
    }


# ============================================================================
# Health - Detailed health information for operators
# ============================================================================

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Detailed health information including database connectivity.",
)
async def health_check(
    request: Request,
    db: Session = Depends(get_db),
) -> HealthResponse:
    """
    Health check endpoint for operators.
    
    Returns comprehensive health information including:
    - API status
    - Database connectivity and response time
    - Environment information
    - Uptime
    - Version
    
    Returns 503 Service Unavailable if the database is unhealthy.
    """
    log = request.state.logger
    
    db_healthy, db_response_ms = check_database_connection_with_timing(db, log)
    uptime_seconds = time.perf_counter() - APP_START_TIME
    
    if not db_healthy:
        log.warning(
            f"Health check failed - database unavailable (response time: {round(db_response_ms, 2)}ms, uptime: {round(uptime_seconds, 1)}s)",
            extra={
                "environment": settings.environment,
            }
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "environment": settings.environment,
                "version": settings.api_version,
                "uptime_seconds": round(uptime_seconds, 1),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
    
    return HealthResponse(
        status="healthy",
        database="connected",
        database_response_ms=round(db_response_ms, 2),
        environment=settings.environment,
        version=settings.api_version,
        uptime_seconds=round(uptime_seconds, 1),
        timestamp=datetime.now(UTC).isoformat(),
    )


# ============================================================================
# Database Health - Database diagnostics for administrators
# ============================================================================

@router.get(
    "/health/database",
    status_code=status.HTTP_200_OK,
    summary="Database health check",
    description="Check database connectivity specifically with performance metrics.",
    include_in_schema=False,
)
async def database_health_check(
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Database-specific health check endpoint.
    
    Returns detailed database connection status and performance metrics.
    This endpoint is intended for administrators and operational monitoring.
    """
    log = request.state.logger
    
    try:
        start_time = time.perf_counter()
        result = db.execute(text("SELECT 1, NOW() as server_time"))
        row = result.first()
        response_time = (time.perf_counter() - start_time) * 1000
        
        server_time = row.server_time if row and hasattr(row, 'server_time') else None
        
        return {
            "status": "healthy",
            "database": "PostgreSQL",
            "response_time_ms": round(response_time, 2),
            "server_time": server_time.isoformat() if server_time else None,
            "connection_pool_size": settings.db_pool_size,
            "environment": settings.environment,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as exc:
        log.exception(
            f"Database health check failed: {type(exc).__name__}"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": "PostgreSQL",
                "environment": settings.environment,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )


# ============================================================================
# Metrics - Operational metrics for monitoring
# ============================================================================

@router.get(
    "/health/metrics",
    status_code=status.HTTP_200_OK,
    summary="Operational metrics",
    description="Get operational metrics for monitoring.",
    include_in_schema=False,
)
async def get_metrics(request: Request) -> Dict[str, Any]:
    """
    Get operational metrics.
    
    Returns:
        Request counts, error rates, response times, and other metrics.
        This endpoint is intended for administrators and operational monitoring.
    """
    log = request.state.logger
    log.info("Metrics requested")
    
    return metrics_collector.get_metrics()