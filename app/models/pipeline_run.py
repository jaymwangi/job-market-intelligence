# app/models/pipeline_run.py
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PipelineRun(Base):
    """
    Tracks ETL pipeline executions for auditing and monitoring.
    """

    __tablename__ = "pipeline_runs"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Execution details
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Status and results
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=text("'running'"),
        index=True,
    )  # running, completed, failed
    records_processed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
    )
    duration_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Source tracking
    source_site: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
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

    # Special indexes
    __table_args__ = (Index("idx_pipeline_runs_started_at_desc", started_at.desc()),)

    def __repr__(self) -> str:
        return f"<PipelineRun(id={self.id}, status={self.status}, source={self.source_site})>"
