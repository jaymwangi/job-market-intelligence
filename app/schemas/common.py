from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response with comprehensive production metrics."""

    status: str = Field(default="healthy", description="API health status")
    database: str = Field(default="connected", description="Database connection status")
    database_response_ms: float | None = Field(
        None, description="Database response time in milliseconds"
    )
    environment: str = Field(..., description="Current environment")
    version: str = Field(default="1.0.0", description="API version")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    timestamp: str = Field(..., description="UTC timestamp of health check")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    detail: str = Field(..., description="Human-readable error message")
    status_code: int = Field(..., description="HTTP status code")
    path: str | None = Field(None, description="Request path")
    timestamp: str = Field(..., description="UTC timestamp of error")
    extra: dict[str, Any] | None = Field(None, description="Additional error context")


class ValidationErrorResponse(BaseModel):
    """Validation error response with field-specific errors."""

    detail: str = Field(default="Validation error", description="Error summary")
    errors: list[dict[str, Any]] = Field(..., description="Field-specific validation errors")
    status_code: int = Field(default=422, description="HTTP status code")
    path: str | None = Field(None, description="Request path")
    timestamp: str = Field(..., description="UTC timestamp of error")


class PaginatedResponse(BaseModel):
    """Base model for paginated responses."""

    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    data: list[Any] = Field(..., description="Items for current page")
