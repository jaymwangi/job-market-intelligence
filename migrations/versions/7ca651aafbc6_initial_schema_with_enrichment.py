"""initial_schema_with_enrichment

Revision ID: 7ca651aafbc6
Revises: 
Create Date: 2026-07-20 16:38:08.928349

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = '7ca651aafbc6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables with enrichment fields."""
    
    # Create jobs table with enrichment columns
    op.create_table(
        'jobs',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('remote_type', sa.String(50), nullable=True),
        sa.Column('salary_min', sa.Numeric(12, 2), nullable=True),
        sa.Column('salary_max', sa.Numeric(12, 2), nullable=True),
        sa.Column('salary_currency', sa.String(10), nullable=True),
        sa.Column('employment_type', sa.String(50), nullable=True),
        sa.Column('experience_level', sa.String(50), nullable=True),
        sa.Column('source_url', sa.String(500), nullable=False),
        sa.Column('source_site', sa.String(50), nullable=False),
        sa.Column('source_id', sa.String(100), nullable=False),
        sa.Column('posted_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scraped_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('raw_data', JSONB(), nullable=True),
        # Sprint 6.6: Enrichment columns
        sa.Column('technology_category', sa.String(50), nullable=True),
        sa.Column('is_tech_role', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('country_code', sa.String(2), nullable=True),
        sa.Column('currency', sa.String(3), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('jobs_pkey')),
        sa.UniqueConstraint('source_site', 'source_id', name=op.f('uq_job_source')),
    )
    
    # Jobs table indexes
    op.create_index('ix_jobs_title', 'jobs', ['title'])
    op.create_index('ix_jobs_source_site', 'jobs', ['source_site'])
    op.create_index('ix_jobs_source_id', 'jobs', ['source_id'])
    op.create_index('ix_jobs_scraped_date', 'jobs', ['scraped_date'])
    op.create_index('ix_jobs_salary_min', 'jobs', ['salary_min'])
    op.create_index('ix_jobs_salary_max', 'jobs', ['salary_max'])
    op.create_index('ix_jobs_remote_type', 'jobs', ['remote_type'])
    op.create_index('ix_jobs_posted_date', 'jobs', ['posted_date'])
    op.create_index('ix_jobs_is_deleted', 'jobs', ['is_deleted'])
    op.create_index('ix_jobs_is_active', 'jobs', ['is_active'])
    op.create_index('ix_jobs_experience_level', 'jobs', ['experience_level'])
    op.create_index('ix_jobs_employment_type', 'jobs', ['employment_type'])
    op.create_index('ix_jobs_company_name', 'jobs', ['company_name'])
    op.create_index('idx_jobs_scraped_date_desc', 'jobs', [sa.text('scraped_date DESC')])
    op.create_index('idx_jobs_salary_range', 'jobs', ['salary_min', 'salary_max'])
    op.create_index('idx_jobs_posted_date_desc', 'jobs', [sa.text('posted_date DESC')])
    # Sprint 6.6: Enrichment indexes
    op.create_index('idx_jobs_country_code', 'jobs', ['country_code'])
    op.create_index('idx_jobs_technology_category', 'jobs', ['technology_category'])
    op.create_index('idx_jobs_is_tech_role', 'jobs', ['is_tech_role'])

    # Create skills table
    op.create_table(
        'skills',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('skills_pkey')),
    )
    op.create_index('ix_skills_name', 'skills', ['name'], unique=True)
    op.create_index('idx_skills_name_lower', 'skills', [sa.text('LOWER(name)')])

    # Create pipeline_runs table
    op.create_table(
        'pipeline_runs',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), server_default=sa.text("'running'"), nullable=False),
        sa.Column('records_processed', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('source_site', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pipeline_runs_pkey')),
    )
    op.create_index('ix_pipeline_runs_status', 'pipeline_runs', ['status'])
    op.create_index('ix_pipeline_runs_started_at', 'pipeline_runs', ['started_at'])
    op.create_index('ix_pipeline_runs_source_site', 'pipeline_runs', ['source_site'])
    op.create_index('idx_pipeline_runs_started_at_desc', 'pipeline_runs', [sa.text('started_at DESC')])

    # Create job_skills junction table
    op.create_table(
        'job_skills',
        sa.Column('job_id', UUID(), nullable=False),
        sa.Column('skill_id', UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], name=op.f('job_skills_job_id_fkey'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], name=op.f('job_skills_skill_id_fkey'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('job_id', 'skill_id', name=op.f('job_skills_pkey')),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('job_skills')
    op.drop_table('pipeline_runs')
    op.drop_table('skills')
    op.drop_table('jobs')