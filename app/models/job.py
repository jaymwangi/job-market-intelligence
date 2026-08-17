"""Job model."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.database.base import Base

# Import for type checking only to avoid circular imports
if TYPE_CHECKING:
    from app.models.skill import Skill


class Job(Base):
    """
    Represents a job posting collected from external job boards.
    """

    __tablename__ = "jobs"

    # ============================================================
    # Primary Key
    # ============================================================
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # ============================================================
    # Core Job Information
    # ============================================================
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # ============================================================
    # Company
    # ============================================================
    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    # ============================================================
    # Location
    # ============================================================
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remote_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    # ============================================================
    # Compensation - using Decimal for precise currency handling
    # ============================================================
    salary_min: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        index=True,
    )
    salary_max: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        index=True,
    )
    # Original posting currency (ISO 4217)
    salary_currency: Mapped[str | None] = mapped_column(
        String(3),
        nullable=True,
        doc="ISO 4217 currency code of the original salary posting",
    )
    # Optional: normalized salary in USD for cross-market comparison
    # TODO: Add after implementing currency normalization
    # salary_usd: Mapped[Decimal | None] = mapped_column(
    #     Numeric(12, 2),
    #     nullable=True,
    #     doc="Salary normalized to USD for cross-market comparison",
    # )

    # ============================================================
    # Employment Details
    # ============================================================
    employment_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    experience_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    # ============================================================
    # Source Tracking - unique constraint prevents duplicates
    # ============================================================
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_site: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    source_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # ============================================================
    # Dates
    # ============================================================
    posted_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    scraped_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # ============================================================
    # Audit Fields
    # ============================================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ============================================================
    # Status
    # ============================================================
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("true"),
        index=True,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        index=True,
    )

    # ============================================================
    # Flexible Data Storage for ETL Resilience
    # ============================================================
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Raw API response data for ETL debugging and resilience",
    )

    # ============================================================
    # Sprint 6.6: Language Support
    # ============================================================
    # Note: No server_default - ETL must provide language
    # Migration removes the default after populating existing rows
    language: Mapped[str] = mapped_column(
        String(2),  # ISO 639-1: 'en', 'fr', 'de', etc.
        nullable=False,
        index=True,
        doc="ISO 639-1 language code (en, fr, de, es, etc.)",
    )

    # ============================================================
    # Sprint 6.6: Technology Classification
    # ============================================================
    is_tech_role: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        index=True,
        doc="Whether this is a technology role",
    )
    technology_category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Primary technology category (backend, frontend, ml_ai, etc.)",
    )
    tech_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Confidence score for technology classification (0.0 - 1.0)",
    )
    matched_tech_terms: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
        doc="Terms that matched during classification (for explainability)",
    )

    # ============================================================
    # Sprint 6.6: Geographic Enrichment
    # ============================================================
    # Country where the job is located (ISO 3166-1 alpha-2)
    country_code: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
        index=True,
        doc="ISO 3166-1 alpha-2 country code where the job is located",
    )

    # ============================================================
    # Relationships
    # ============================================================
    skills: Mapped[list["Skill"]] = relationship(
        "Skill",
        secondary="job_skills",
        back_populates="jobs",
        lazy="selectin",
    )

    # ============================================================
    # Validators
    # ============================================================

    @validates("tech_confidence")
    def validate_confidence(self, key: str, value: float | None) -> float | None:
        """Validate tech_confidence is between 0.0 and 1.0."""
        if value is not None and not (0.0 <= value <= 1.0):
            raise ValueError("tech_confidence must be between 0.0 and 1.0")
        return value

    @validates("salary_currency")
    def validate_salary_currency(self, key: str, value: str | None) -> str | None:
        """Validate salary_currency is a 3-letter ISO 4217 code."""
        if value is not None and len(value) != 3:
            raise ValueError("salary_currency must be a 3-letter ISO 4217 code")
        return value.upper() if value else None

    @validates("country_code")
    def validate_country_code(self, key: str, value: str | None) -> str | None:
        """Validate country_code is a 2-letter ISO 3166-1 alpha-2 code."""
        if value is not None and len(value) != 2:
            raise ValueError("country_code must be a 2-letter ISO 3166-1 alpha-2 code")
        return value.upper() if value else None

    # ============================================================
    # Table Constraints and Special Indexes
    # ============================================================
    __table_args__ = (
        # Prevent duplicate jobs from the same source
        UniqueConstraint(
            "source_site",
            "source_id",
            name="uq_job_source",
        ),
        # Check constraints for data integrity
        CheckConstraint(
            "tech_confidence IS NULL OR "
            "(tech_confidence >= 0.0 AND tech_confidence <= 1.0)",
            name="ck_job_tech_confidence",
        ),
        CheckConstraint(
            "country_code IS NULL OR length(country_code) = 2",
            name="ck_job_country_code",
        ),
        CheckConstraint(
            "salary_currency IS NULL OR length(salary_currency) = 3",
            name="ck_job_salary_currency",
        ),
        # Indexes - using ix_ prefix for consistency with SQLAlchemy default
        Index("ix_jobs_posted_date_desc", posted_date.desc()),
        Index("ix_jobs_scraped_date_desc", scraped_date.desc()),
        Index("ix_jobs_salary_range", salary_min, salary_max),
        # Composite index for common filter pattern: tech roles by language
        Index("ix_jobs_language_is_tech_role", language, is_tech_role),
    )

    def __repr__(self) -> str:
        """Return a string representation of the Job."""
        title = self.title[:50] if self.title else ""
        company = self.company_name or ""
        return (
            f"<Job("
            f"id={self.id}, "
            f"title={title!r}, "
            f"company={company!r}, "
            f"source={self.source_site!r}, "
            f"language={self.language!r}, "
            f"is_tech={self.is_tech_role}"
            f")>"
        )