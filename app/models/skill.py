# app/models/skill.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func, text, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# Import for type checking only to avoid circular imports
if TYPE_CHECKING:
    from app.models.job import Job


class Skill(Base):
    """
    Represents a skill that can be associated with job postings.
    Skills are normalized (e.g., "Python" instead of "python", "py").
    """
    __tablename__ = "skills"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Skill name (normalized, unique)
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
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

    # Relationships - using string forward references
    jobs: Mapped[list["Job"]] = relationship(
        "Job",  # String forward reference
        secondary="job_skills",
        back_populates="skills",
        lazy="selectin",
    )

    # Special indexes
    __table_args__ = (
        Index("idx_skills_name_lower", func.lower(name)),  # Case-insensitive lookups
    )

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name={self.name})>"