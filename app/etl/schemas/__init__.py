"""ETL schemas - typed data contracts between pipeline stages.

This package defines the Pydantic schemas used throughout the ETL pipeline:

Pipeline Flow:
    Raw Data → JobValidated → JobTransformed → JobEnriched → Database

Sprint 6.6 adds:
    - language: ISO 639-1 language code
    - technology_category: Primary technology category
    - is_tech_role: Whether the job is a technology role
    - tech_confidence: Confidence score for technology classification
    - matched_tech_terms: Terms that matched during classification
    - country_code: ISO 3166-1 alpha-2 country code
    - normalized_salary_min: Salary normalized to USD
    - normalized_salary_max: Salary normalized to USD

Schemas:
    - JobValidated: Raw job data after validation
    - JobTransformed: Normalized job data after transformation
    - JobEnriched: Job data after enrichment (language, skills, tech, geo)
    - PipelineMetrics: Metrics for pipeline execution tracking
"""

# ============================================================
# Core Schemas
# ============================================================

# Transformed schema - normalized job data
from app.etl.schemas.transformed import JobTransformed

# Enriched schema - with intelligence data (Sprint 6.6)
from app.etl.schemas.enriched import (
    JobEnriched,
    TechnologyCategory as EnrichedTechnologyCategory,
)

# Validated schema - raw job data after validation
from app.etl.schemas.validated import JobValidated

# Pipeline metrics - execution tracking
from app.etl.schemas.metrics import PipelineMetrics


# ============================================================
# __all__ - Public API (Alphabetized)
# ============================================================

__all__ = [
    # Core Schemas
    "JobEnriched",
    "JobTransformed",
    "JobValidated",
    "PipelineMetrics",
    
    # Enriched Types (Sprint 6.6)
    "EnrichedTechnologyCategory",
]