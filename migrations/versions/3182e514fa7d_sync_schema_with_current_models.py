"""sync schema with current models

Revision ID: 3182e514fa7d
Revises: 7ca651aafbc6
Create Date: 2026-08-21 10:59:42.769797
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3182e514fa7d"
down_revision: Union[str, Sequence[str], None] = "7ca651aafbc6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ================================================================
    # jobs
    # ================================================================

    # Migrate existing currency data before removing the legacy column.
    op.execute(
        """
        UPDATE jobs
        SET salary_currency = currency
        WHERE salary_currency IS NULL
          AND currency IS NOT NULL
        """
    )

    # Previous: VARCHAR(10)
    # Current:  VARCHAR(3)
    op.alter_column(
        "jobs",
        "salary_currency",
        existing_type=sa.VARCHAR(length=10),
        type_=sa.String(length=3),
        existing_nullable=True,
    )

    # Add language for existing rows.
    # Temporary server default allows existing rows to receive 'en'.
    op.add_column(
        "jobs",
        sa.Column(
            "language",
            sa.String(length=2),
            server_default=sa.text("'en'"),
            nullable=False,
        ),
    )

    # Current SQLAlchemy model has no server_default.
    op.alter_column(
        "jobs",
        "language",
        existing_type=sa.String(length=2),
        existing_nullable=False,
        server_default=None,
    )

    # ------------------------------------------------
    # Replace legacy job indexes
    # ------------------------------------------------

    op.drop_index(
        op.f("idx_jobs_country_code"),
        table_name="jobs",
    )

    op.drop_index(
        op.f("idx_jobs_is_tech_role"),
        table_name="jobs",
    )

    op.drop_index(
        op.f("idx_jobs_posted_date_desc"),
        table_name="jobs",
    )

    op.drop_index(
        op.f("idx_jobs_salary_range"),
        table_name="jobs",
    )

    op.drop_index(
        op.f("idx_jobs_scraped_date_desc"),
        table_name="jobs",
    )

    op.drop_index(
        op.f("idx_jobs_technology_category"),
        table_name="jobs",
    )

    # ------------------------------------------------
    # Create indexes matching current Job model
    # ------------------------------------------------

    op.create_index(
        op.f("ix_jobs_country_code"),
        "jobs",
        ["country_code"],
        unique=False,
    )

    op.create_index(
        op.f("ix_jobs_is_tech_role"),
        "jobs",
        ["is_tech_role"],
        unique=False,
    )

    op.create_index(
        op.f("ix_jobs_language"),
        "jobs",
        ["language"],
        unique=False,
    )

    op.create_index(
        "ix_jobs_language_is_tech_role",
        "jobs",
        ["language", "is_tech_role"],
        unique=False,
    )

    op.create_index(
        "ix_jobs_posted_date_desc",
        "jobs",
        [sa.literal_column("posted_date DESC")],
        unique=False,
    )

    op.create_index(
        "ix_jobs_salary_range",
        "jobs",
        ["salary_min", "salary_max"],
        unique=False,
    )

    op.create_index(
        "ix_jobs_scraped_date_desc",
        "jobs",
        [sa.literal_column("scraped_date DESC")],
        unique=False,
    )

    op.create_index(
        op.f("ix_jobs_technology_category"),
        "jobs",
        ["technology_category"],
        unique=False,
    )

    # Remove legacy currency column.
    op.drop_column(
        "jobs",
        "currency",
    )

    # ================================================================
    # pipeline_runs
    # ================================================================

    # No migration required.
    #
    # The initial migration already creates:
    #
    #   ix_pipeline_runs_status
    #   ix_pipeline_runs_started_at
    #   ix_pipeline_runs_source_site
    #   idx_pipeline_runs_started_at_desc
    #
    # These match the current PipelineRun model.


    # ================================================================
    # skills
    # ================================================================

    # No migration required.
    #
    # The initial migration already creates:
    #
    #   ix_skills_name UNIQUE
    #   idx_skills_name_lower
    #
    # These match the current Skill model.


def downgrade() -> None:
    """Downgrade schema."""

    # ================================================================
    # jobs
    # ================================================================

    # Restore legacy currency column.
    op.add_column(
        "jobs",
        sa.Column(
            "currency",
            sa.VARCHAR(length=3),
            autoincrement=False,
            nullable=True,
        ),
    )

    # Restore currency values.
    op.execute(
        """
        UPDATE jobs
        SET currency = salary_currency
        WHERE salary_currency IS NOT NULL
        """
    )

    # Remove indexes introduced by this migration.
    op.drop_index(
        op.f("ix_jobs_technology_category"),
        table_name="jobs",
    )

    op.drop_index(
        "ix_jobs_scraped_date_desc",
        table_name="jobs",
    )

    op.drop_index(
        "ix_jobs_salary_range",
        table_name="jobs",
    )

    op.drop_index(
        "ix_jobs_posted_date_desc",
        table_name="jobs",
    )

    op.drop_index(
        "ix_jobs_language_is_tech_role",
        table_name="jobs",
    )

    op.drop_index(
        op.f("ix_jobs_language"),
        table_name="jobs",
    )

    op.drop_index(
        op.f("ix_jobs_is_tech_role"),
        table_name="jobs",
    )

    op.drop_index(
        op.f("ix_jobs_country_code"),
        table_name="jobs",
    )

    # Restore legacy indexes.
    op.create_index(
        op.f("idx_jobs_technology_category"),
        "jobs",
        ["technology_category"],
        unique=False,
    )

    op.create_index(
        op.f("idx_jobs_scraped_date_desc"),
        "jobs",
        [sa.literal_column("scraped_date DESC")],
        unique=False,
    )

    op.create_index(
        op.f("idx_jobs_salary_range"),
        "jobs",
        ["salary_min", "salary_max"],
        unique=False,
    )

    op.create_index(
        op.f("idx_jobs_posted_date_desc"),
        "jobs",
        [sa.literal_column("posted_date DESC")],
        unique=False,
    )

    op.create_index(
        op.f("idx_jobs_is_tech_role"),
        "jobs",
        ["is_tech_role"],
        unique=False,
    )

    op.create_index(
        op.f("idx_jobs_country_code"),
        "jobs",
        ["country_code"],
        unique=False,
    )

    # Remove language.
    op.drop_column(
        "jobs",
        "language",
    )

    # Restore original salary_currency type.
    op.alter_column(
        "jobs",
        "salary_currency",
        existing_type=sa.String(length=3),
        type_=sa.VARCHAR(length=10),
        existing_nullable=True,
    )