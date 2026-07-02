# app/schemas/common.py
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"