"""End-to-end ETL workflow tests."""

import pytest

from app.etl import ETLPipeline
from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.skill import Skill


@pytest.fixture
def e2e_raw_jobs():
    """Controlled raw jobs used to validate the complete ETL path."""
    return [
        {
            "id": "e2e-etl-001",
            "title": "Senior Python Backend Engineer",
            "description": (
                "Build APIs using Python, FastAPI, PostgreSQL, Docker, "
                "and AWS."
            ),
            "company": {"display_name": "E2E Tech"},
            "location": {"display_name": "Nairobi, Kenya"},
            "created": "2026-09-04T06:00:00Z",
            "redirect_url": "https://example.com/e2e-etl-001",
            "contract_type": "full_time",
            "category": {"label": "IT Jobs"},
            "salary": {
                "min": 120000,
                "max": 180000,
                "currency": "USD",
            },
        },
        {
            "id": "e2e-etl-002",
            "title": "Business Operations Coordinator",
            "description": (
                "Coordinate business operations, reporting, and "
                "administrative activities."
            ),
            "company": {"display_name": "E2E Operations"},
            "location": {"display_name": "Nairobi, Kenya"},
            "created": "2026-09-04T07:00:00Z",
            "redirect_url": "https://example.com/e2e-etl-002",
            "contract_type": "full_time",
            "category": {"label": "Other"},
            "salary": {
                "min": 60000,
                "max": 90000,
                "currency": "USD",
            },
        },
    ]


def _delete_e2e_jobs(db_session, source_ids: list[str]) -> None:
    """Remove controlled E2E jobs and their relationships."""
    jobs = (
        db_session.query(Job)
        .filter(
            Job.source_site == "adzuna",
            Job.source_id.in_(source_ids),
        )
        .all()
    )

    job_ids = [job.id for job in jobs]

    if job_ids:
        db_session.query(JobSkill).filter(
            JobSkill.job_id.in_(job_ids)
        ).delete(synchronize_session=False)

        db_session.query(Job).filter(
            Job.id.in_(job_ids)
        ).delete(synchronize_session=False)

    db_session.flush()


def test_etl_to_database_persists_complete_job_data(
    monkeypatch,
    e2e_raw_jobs,
    db_session,
):
    """ETL loads controlled data and persists its enriched results."""
    source_ids = [job["id"] for job in e2e_raw_jobs]

    _delete_e2e_jobs(db_session, source_ids)

    pipeline = ETLPipeline(db_session=db_session)

    monkeypatch.setattr(
        pipeline.extractor,
        "extract",
        lambda country: e2e_raw_jobs,
    )

    try:
        metrics = pipeline.run(
            countries=["ke"],
            use_acquisition=False,
        )

        assert metrics.extracted == 2
        assert metrics.transformed == 2
        assert metrics.enriched == 2
        assert metrics.validated == 2
        assert metrics.inserted == 2

        jobs = (
            db_session.query(Job)
            .filter(
                Job.source_site == "adzuna",
                Job.source_id.in_(source_ids),
            )
            .all()
        )

        assert len(jobs) == 2

        tech_job = next(
            job
            for job in jobs
            if job.source_id == "e2e-etl-001"
        )

        non_tech_job = next(
            job
            for job in jobs
            if job.source_id == "e2e-etl-002"
        )

        # Core fields persisted.
        assert tech_job.title == "Senior Python Backend Engineer"
        assert tech_job.company_name == "E2E Tech"
        assert tech_job.location == "Nairobi, Kenya"

        # Enrichment persisted.
        assert tech_job.country_code == "KE"
        assert tech_job.salary_currency == "USD"
        assert tech_job.language == "en"

        # Classification persisted.
        assert tech_job.is_tech_role is True
        assert tech_job.technology_category == "backend"

        assert non_tech_job.is_tech_role is False
        assert non_tech_job.technology_category is None

        # Skills persisted through job-skill relationships.
        skill_names = {
            skill.name.lower()
            for skill in db_session.query(Skill).all()
        }

        assert "python" in skill_names

        relationship_count = (
            db_session.query(JobSkill)
            .filter(JobSkill.job_id == tech_job.id)
            .count()
        )

        assert relationship_count > 0

    finally:
        _delete_e2e_jobs(db_session, source_ids)


def test_etl_database_state_is_queryable(
    monkeypatch,
    e2e_raw_jobs,
    db_session,
):
    """Data produced by ETL is immediately queryable from PostgreSQL."""
    source_ids = [job["id"] for job in e2e_raw_jobs]

    _delete_e2e_jobs(db_session, source_ids)

    pipeline = ETLPipeline(db_session=db_session)

    monkeypatch.setattr(
        pipeline.extractor,
        "extract",
        lambda country: e2e_raw_jobs,
    )

    try:
        pipeline.run(
            countries=["ke"],
            use_acquisition=False,
        )

        total = (
            db_session.query(Job)
            .filter(Job.source_id.in_(source_ids))
            .count()
        )

        tech_total = (
            db_session.query(Job)
            .filter(
                Job.source_id.in_(source_ids),
                Job.is_tech_role.is_(True),
            )
            .count()
        )

        assert total == 2
        assert tech_total == 1

    finally:
        _delete_e2e_jobs(db_session, source_ids)