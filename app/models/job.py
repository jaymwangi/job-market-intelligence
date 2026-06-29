# app/models/job.py
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Numeric,
    String,
    Text,
    func,
    text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# Import for type checking only to avoid circular imports
if TYPE_CHECKING:
    from app.models.skill import Skill


class Job(Base):
    """
    Represents a job posting collected from external job boards.
    """
    __tablename__ = "jobs"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Core job information
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Company
    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    # Location
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    remote_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    # Compensation - using Decimal for precise currency handling
    salary_min: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        index=True,
    )
    salary_max: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        index=True,
    )
    salary_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Employment details
    employment_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    experience_level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    # Source tracking - unique constraint prevents duplicates
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

    # Dates
    posted_date: Mapped[Optional[datetime]] = mapped_column(
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

    # Audit fields
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

    # Status - using text() for server defaults
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

    # Flexible data storage for ETL resilience (PostgreSQL-specific)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships - using string forward references
    skills: Mapped[list["Skill"]] = relationship(
        "Skill",  # String forward reference
        secondary="job_skills",
        back_populates="jobs",
        lazy="selectin",
    )

    # Table constraints and special indexes
    __table_args__ = (
        # Prevent duplicate jobs from the same source
        UniqueConstraint(
            "source_site",
            "source_id",
            name="uq_job_source",
        ),
        # Special indexes for complex queries
        Index("idx_jobs_posted_date_desc", posted_date.desc()),
        Index("idx_jobs_scraped_date_desc", scraped_date.desc()),
        Index("idx_jobs_salary_range", salary_min, salary_max),
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title={self.title}, company={self.company_name})>"