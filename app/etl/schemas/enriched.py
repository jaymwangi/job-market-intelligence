"""Enriched job schema - adds intelligence data."""

from enum import StrEnum
from typing import Annotated, Self

from annotated_types import MaxLen
from pydantic import ConfigDict, Field, field_validator, model_validator

from app.etl.schemas.transformed import JobTransformed
from app.etl.enrichment.data.technology_categories import (
    TechnologyCategory,
    get_skill_display_name,
    normalize_skills_list,
)


class JobEnriched(JobTransformed):
    """
    Enriched job schema with intelligence data.
    
    This schema represents a job after the enrichment layer has added:
    - Language detection
    - Skill extraction
    - Technology classification
    - Geographic enrichment
    - Salary normalization
    
    Validation rules:
    - Tech roles must have a technology_category and tech_confidence
    - Non-tech roles cannot have tech classification fields set
    - Skills and matched_tech_terms are normalized and deduplicated
    """

    # ============================================================
    # Sprint 6.6: Language Support
    # ============================================================
    language: str = Field(
        default="en",
        description="ISO 639-1 language code (en, fr, de, es, etc.)",
        min_length=2,
        max_length=2,
    )

    # ============================================================
    # Sprint 6.6: Skill Extraction
    # ============================================================
    skills: Annotated[list[str], MaxLen(50)] = Field(
        default_factory=list,
        description="Extracted skills (normalized display names, max 50)",
    )

    # ============================================================
    # Sprint 6.6: Technology Classification
    # ============================================================
    technology_category: TechnologyCategory | None = Field(
        default=None,
        description="Primary technology category (must be valid enum value)",
    )
    is_tech_role: bool = Field(
        default=False,
        description="Whether this is a technology role",
    )
    tech_confidence: float | None = Field(
        default=None,
        description="Confidence score for technology classification (0.0 - 1.0)",
        ge=0.0,
        le=1.0,
    )
    matched_tech_terms: Annotated[list[str], MaxLen(20)] = Field(
        default_factory=list,
        description="Terms that matched during classification (normalized, max 20)",
    )

    # ============================================================
    # Sprint 6.6: Geographic Enrichment
    # ============================================================
    country_code: str | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country code where the job is located",
        min_length=2,
        max_length=2,
    )

    # ============================================================
    # Sprint 6.6: Salary Normalization
    # ============================================================
    currency: str | None = Field(
        default=None,
        description="Salary currency (ISO 4217)",
        min_length=3,
        max_length=3,
    )
    
    normalized_salary_min: float | None = Field(
        default=None,
        description="Normalized minimum salary (USD if normalization enabled)",
        ge=0.0,
    )
    
    normalized_salary_max: float | None = Field(
        default=None,
        description="Normalized maximum salary (USD if normalization enabled)",
        ge=0.0,
    )

    # ============================================================
    # Field Validators
    # ============================================================

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate and normalize language to lowercase."""
        if len(v) != 2 or not v.isalpha():
            raise ValueError("language must be a 2-letter ISO 639-1 code")
        return v.strip().lower()

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v: str | None) -> str | None:
        """Validate and normalize country_code to uppercase."""
        if v is not None:
            if len(v) != 2 or not v.isalpha():
                raise ValueError("country_code must be a 2-letter ISO 3166-1 alpha-2 code")
            return v.strip().upper()
        return v

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, v: list[str]) -> list[str]:
        """Normalize skills to display names, deduplicate, and sort."""
        return normalize_skills_list(v)

    @field_validator("matched_tech_terms")
    @classmethod
    def normalize_matched_terms(cls, v: list[str]) -> list[str]:
        """Normalize matched_tech_terms, deduplicate, and sort."""
        if not v:
            return []
        
        # Strip whitespace and convert to lowercase for matching
        normalized = []
        seen = set()
        
        for term in v:
            if not term or not term.strip():
                continue
            
            display = get_skill_display_name(term)
            key = display.lower()
            
            if key not in seen:
                seen.add(key)
                normalized.append(display)
        
        return sorted(normalized)

    @field_validator("tech_confidence")
    @classmethod
    def validate_tech_confidence(cls, v: float | None) -> float | None:
        """Validate tech_confidence is between 0.0 and 1.0."""
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("tech_confidence must be between 0.0 and 1.0")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        """Validate and normalize currency to uppercase."""
        if v is not None:
            if len(v) != 3 or not v.isalpha():
                raise ValueError("currency must be a 3-letter ISO 4217 code")
            return v.strip().upper()
        return v

    @field_validator("normalized_salary_min", "normalized_salary_max")
    @classmethod
    def validate_normalized_salary(cls, v: float | None) -> float | None:
        """Validate normalized salary is non-negative."""
        if v is not None and v < 0:
            raise ValueError("normalized_salary must be >= 0")
        return v

    # ============================================================
    # Model Validator - Cross-field validation
    # ============================================================

    @model_validator(mode="after")
    def validate_consistency(self) -> Self:
        """
        Enforce consistency between tech classification fields.
        
        Rules:
        - Tech roles (is_tech_role=True):
            - Must have technology_category set
            - Must have tech_confidence set
            - Should have matched_tech_terms (but not required)
        
        - Non-tech roles (is_tech_role=False):
            - Must NOT have technology_category set
            - Must NOT have tech_confidence set
            - Must NOT have matched_tech_terms
        """
        if self.is_tech_role:
            # Tech role validation
            if self.technology_category is None:
                raise ValueError(
                    "technology_category is required when is_tech_role is True"
                )
            if self.tech_confidence is None:
                raise ValueError(
                    "tech_confidence is required when is_tech_role is True"
                )
        else:
            # Non-tech role validation - fail fast on inconsistent data
            errors = []
            
            if self.technology_category is not None:
                errors.append(
                    f"technology_category must be None for non-tech jobs "
                    f"(got: {self.technology_category})"
                )
            if self.tech_confidence is not None:
                errors.append(
                    f"tech_confidence must be None for non-tech jobs "
                    f"(got: {self.tech_confidence})"
                )
            if self.matched_tech_terms:
                errors.append(
                    f"matched_tech_terms must be empty for non-tech jobs "
                    f"(got: {self.matched_tech_terms})"
                )
            
            if errors:
                raise ValueError("; ".join(errors))
        
        return self

    # ============================================================
    # Pydantic v2 Configuration
    # ============================================================

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "title": "Senior Backend Engineer",
                    "description": "Build scalable APIs using Python and Django",
                    "company_name": "Tech Corp",
                    "location": "San Francisco, CA",
                    "salary_min": 120000.00,
                    "salary_max": 180000.00,
                    "salary_currency": "USD",
                    "source_url": "https://example.com/job/123",
                    "source_site": "adzuna",
                    "source_id": "abc123",
                    "posted_date": "2024-01-15T10:00:00Z",
                    "scraped_date": "2024-01-15T12:00:00Z",
                    "language": "en",
                    "skills": ["Python", "Django", "PostgreSQL", "Docker", "AWS"],
                    "technology_category": "backend",
                    "is_tech_role": True,
                    "tech_confidence": 0.92,
                    "matched_tech_terms": ["Python", "Django", "API", "Microservices"],
                    "country_code": "US",
                    "currency": "USD",
                    "normalized_salary_min": 120000.00,
                    "normalized_salary_max": 180000.00,
                },
                {
                    "title": "Sales Manager",
                    "description": "Lead sales team and drive revenue growth",
                    "company_name": "Sales Corp",
                    "location": "New York, NY",
                    "salary_min": 80000.00,
                    "salary_max": 120000.00,
                    "salary_currency": "USD",
                    "source_url": "https://example.com/job/456",
                    "source_site": "adzuna",
                    "source_id": "def456",
                    "posted_date": "2024-01-15T10:00:00Z",
                    "scraped_date": "2024-01-15T12:00:00Z",
                    "language": "en",
                    "skills": ["Sales", "Management", "Leadership"],
                    "is_tech_role": False,
                    "country_code": "US",
                    "currency": "USD",
                    "normalized_salary_min": 80000.00,
                    "normalized_salary_max": 120000.00,
                },
            ]
        },
    )