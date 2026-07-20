"""Pipeline metrics schema."""

from pydantic import BaseModel, Field


class PipelineMetrics(BaseModel):
    """Metrics from ETL pipeline run."""

    extracted: int = Field(default=0, description="Number of raw jobs extracted")
    transformed: int = Field(default=0, description="Number of jobs transformed")
    enriched: int = Field(default=0, description="Number of jobs enriched")
    validated: int = Field(default=0, description="Number of jobs validated")

    inserted: int = Field(default=0, description="Number of new jobs inserted")
    updated: int = Field(default=0, description="Number of existing jobs updated")
    failed: int = Field(default=0, description="Number of jobs that failed")
    purged: int = Field(default=0, description="Number of old jobs purged")

    skills_added: int = Field(
        default=0,
        description="Number of new skills added",
    )
    relationships_added: int = Field(
        default=0,
        description="Number of job-skill relationships added",
    )

    duration_seconds: float = Field(
        default=0.0,
        description="Total ETL pipeline execution duration in seconds",
    )

    def total_processed(self) -> int:
        """Total number of jobs processed."""
        return self.extracted

    def total_loaded(self) -> int:
        """Total number of jobs loaded (inserted + updated)."""
        return self.inserted + self.updated

    def success_rate(self) -> float:
        """Success rate as a percentage."""
        total = self.total_processed()
        if total == 0:
            return 100.0
        return (self.validated / total) * 100.0