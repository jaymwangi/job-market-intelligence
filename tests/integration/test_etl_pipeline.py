# tests/integration/test_etl_pipeline.py

"""Integration tests for the complete ETL pipeline."""

import pytest

from app.etl import ETLPipeline
from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.skill import Skill


@pytest.fixture
def sample_raw_jobs():
    """Return representative Adzuna-style raw jobs."""
    return [
        {
            "id": "integration-etl-001",
            "title": "Senior Python Backend Engineer",
            "description": (
                "Build scalable APIs with Python, FastAPI, PostgreSQL, "
                "Docker, and AWS."
            ),
            "company": {"display_name": "Integration Tech"},
            "location": {"display_name": "Nairobi, Kenya"},
            "created": "2026-08-27T06:00:00Z",
            "redirect_url": (
                "https://example.com/jobs/integration-etl-001"
            ),
            "contract_type": "full_time",
            "category": {"label": "IT Jobs"},
            "salary": {
                "min": 120000,
                "max": 180000,
                "currency": "USD",
            },
        },
        {
            "id": "integration-etl-002",
            "title": "Data Analyst",
            "description": (
                "Analyze business data using SQL, Python, Power BI, "
                "and data visualization."
            ),
            "company": {"display_name": "Analytics Corp"},
            "location": {"display_name": "Nairobi, Kenya"},
            "created": "2026-08-27T07:00:00Z",
            "redirect_url": (
                "https://example.com/jobs/integration-etl-002"
            ),
            "contract_type": "full_time",
            "category": {"label": "IT Jobs"},
            "salary": {
                "min": 80000,
                "max": 120000,
                "currency": "USD",
            },
        },
    ]


def _delete_test_jobs(
    db_session,
    source_ids: list[str],
) -> None:
    """Remove integration-test jobs using the test database session."""
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
        ).delete(
            synchronize_session=False
        )

        db_session.query(Job).filter(
            Job.id.in_(job_ids)
        ).delete(
            synchronize_session=False
        )

    db_session.flush()


def _get_test_jobs(
    db_session,
    source_ids: list[str],
) -> list[Job]:
    """Fetch integration-test jobs using the test database session."""
    return (
        db_session.query(Job)
        .filter(
            Job.source_site == "adzuna",
            Job.source_id.in_(source_ids),
        )
        .all()
    )


def _get_test_skills(
    db_session,
) -> list[Skill]:
    """Fetch skills using the test database session."""
    return db_session.query(Skill).all()


def _count_test_relationships(
    db_session,
    job_ids: list,
) -> int:
    """Count job-skill relationships using the test database session."""
    return db_session.query(JobSkill).filter(
        JobSkill.job_id.in_(job_ids)
    ).count()


def test_etl_pipeline_processes_and_persists_jobs(
    monkeypatch,
    sample_raw_jobs,
    db_session,
):
    """The complete legacy ETL path transforms and persists valid jobs."""
    source_ids = [job["id"] for job in sample_raw_jobs]

    _delete_test_jobs(db_session, source_ids)

    pipeline = ETLPipeline(db_session=db_session)

    monkeypatch.setattr(
        pipeline.extractor,
        "extract",
        lambda country: sample_raw_jobs,
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
        assert metrics.updated == 0

        persisted_jobs = _get_test_jobs(
            db_session,
            source_ids,
        )

        assert len(persisted_jobs) == 2

        titles = {job.title for job in persisted_jobs}

        assert titles == {
            "Senior Python Backend Engineer",
            "Data Analyst",
        }

        senior_backend_job = next(
            job
            for job in persisted_jobs
            if job.source_id == "integration-etl-001"
        )

        data_analyst_job = next(
            job
            for job in persisted_jobs
            if job.source_id == "integration-etl-002"
        )

        # Verify persisted technology classification.
        assert senior_backend_job.is_tech_role is True
        assert senior_backend_job.technology_category == "backend"

        # Data Analyst is classified as non-tech under the
        # current technology classification policy.
        assert data_analyst_job.is_tech_role is False
        assert data_analyst_job.technology_category is None

        # Verify persisted country normalization.
        assert senior_backend_job.country_code == "KE"
        assert data_analyst_job.country_code == "KE"

        # Verify the original salary currency survives persistence.
        assert senior_backend_job.salary_currency == "USD"
        assert data_analyst_job.salary_currency == "USD"

        persisted_skills = _get_test_skills(db_session)

        skill_names = {
            skill.name.lower()
            for skill in persisted_skills
        }

        assert "python" in skill_names
        assert "sql" in skill_names

        relationship_count = _count_test_relationships(
            db_session,
            [job.id for job in persisted_jobs],
        )

        assert relationship_count > 0

    finally:
        _delete_test_jobs(
            db_session,
            source_ids,
        )

def test_etl_pipeline_propagates_extraction_failure(
    monkeypatch,
):
    """The pipeline propagates extraction failures to the caller."""
    pipeline = ETLPipeline()

    expected_error = RuntimeError(
        "Simulated extraction failure"
    )

    def fail_extract(country):
        raise expected_error

    monkeypatch.setattr(
        pipeline.extractor,
        "extract",
        fail_extract,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated extraction failure",
    ):
        pipeline.run(
            countries=["ke"],
            use_acquisition=False,
        )


def test_etl_pipeline_handles_empty_extraction(
    monkeypatch,
):
    """The pipeline completes safely when no jobs are extracted."""
    pipeline = ETLPipeline()

    monkeypatch.setattr(
        pipeline.extractor,
        "extract",
        lambda country: [],
    )

    metrics = pipeline.run(
        countries=["ke"],
        use_acquisition=False,
    )

    assert metrics.extracted == 0
    assert metrics.transformed == 0
    assert metrics.enriched == 0
    assert metrics.validated == 0
    assert metrics.inserted == 0
    assert metrics.updated == 0
    assert metrics.duration_seconds is not None
    assert metrics.duration_seconds >= 0


def test_etl_pipeline_upserts_existing_jobs(
    monkeypatch,
    sample_raw_jobs,
    db_session,
):
    """Running the same ETL input twice updates rather than duplicates."""
    source_ids = [job["id"] for job in sample_raw_jobs]

    _delete_test_jobs(
        db_session,
        source_ids,
    )

    pipeline = ETLPipeline(db_session=db_session)

    monkeypatch.setattr(
        pipeline.extractor,
        "extract",
        lambda country: sample_raw_jobs,
    )

    try:
        first_metrics = pipeline.run(
            countries=["ke"],
            use_acquisition=False,
        )

        assert first_metrics.inserted == 2
        assert first_metrics.updated == 0

        original_job = next(
            job
            for job in _get_test_jobs(db_session, source_ids)
            if job.source_id == "integration-etl-001"
        )

        original_id = original_job.id
        original_source_id = original_job.source_id

        updated_raw_jobs = [
            {
                **job,
                "title": (
                    "Updated Integration Test Job"
                    if job["id"] == "integration-etl-001"
                    else job["title"]
                ),
            }
            for job in sample_raw_jobs
        ]

        monkeypatch.setattr(
            pipeline.extractor,
            "extract",
            lambda country: updated_raw_jobs,
        )

        second_metrics = pipeline.run(
            countries=["ke"],
            use_acquisition=False,
        )

        assert second_metrics.inserted == 0
        assert second_metrics.updated == 2

        # Force SQLAlchemy to reload ORM state from the
        # Core-level upsert.
        db_session.expire_all()

        persisted_jobs = _get_test_jobs(
            db_session,
            source_ids,
        )

        assert len(persisted_jobs) == 2

        updated_job = next(
            job
            for job in persisted_jobs
            if job.source_id == original_source_id
        )

        assert updated_job.id == original_id
        assert updated_job.title == "Updated Integration Test Job"

    finally:
        _delete_test_jobs(
            db_session,
            source_ids,
        )