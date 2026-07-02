# app/schemas/common.py
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="healthy", description="API health status")
    database: str = Field(default="connected", description="Database connection status")
    environment: str = Field(..., description="Current environment")
    timestamp: str = Field(..., description="UTC timestamp of health check")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str = Field(..., description="Human-readable error message")
    status_code: int = Field(..., description="HTTP status code")
    path: Optional[str] = Field(None, description="Request path")
    timestamp: str = Field(..., description="UTC timestamp of error")
    extra: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class ValidationErrorResponse(BaseModel):
    """Validation error response with field-specific errors."""
    detail: str = Field(default="Validation error", description="Error summary")
    errors: List[Dict[str, Any]] = Field(..., description="Field-specific validation errors")
    status_code: int = Field(default=422, description="HTTP status code")
    path: Optional[str] = Field(None, description="Request path")
    timestamp: str = Field(..., description="UTC timestamp of error")


class PaginatedResponse(BaseModel):
    """Base model for paginated responses."""
    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    data: List[Any] = Field(..., description="Items for current page")