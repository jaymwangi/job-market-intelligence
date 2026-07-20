"""Validated job schema - final form before loading."""

from typing import Optional, List
from datetime import datetime
from pydantic import Field
from app.etl.schemas.enriched import JobEnriched


class JobValidated(JobEnriched):
    """Validated job - ready for loading."""

    # Additional validation metadata
    validation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when validation occurred",
    )
    validation_warnings: List[str] = Field(
        default_factory=list,
        description="Any validation warnings",
    )