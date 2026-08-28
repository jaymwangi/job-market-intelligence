"""add tech confidence to jobs

Revision ID: 74b5dc797be3
Revises: 3182e514fa7d
Create Date: 2026-08-27 10:16:29.191382

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "74b5dc797be3"
down_revision: Union[str, Sequence[str], None] = "3182e514fa7d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "jobs",
        sa.Column("tech_confidence", sa.Float(), nullable=True),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "matched_tech_terms",
            postgresql.ARRAY(sa.Text()),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "ck_job_tech_confidence",
        "jobs",
        "tech_confidence IS NULL OR "
        "(tech_confidence >= 0.0 AND tech_confidence <= 1.0)",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_job_tech_confidence",
        "jobs",
        type_="check",
    )
    op.drop_column("jobs", "matched_tech_terms")
    op.drop_column("jobs", "tech_confidence")