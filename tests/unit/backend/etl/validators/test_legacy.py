from datetime import datetime, timezone
from typing import Any

import pytest
from pydantic import ValidationError

from app.etl.validators.legacy import (
    JobValidatedModel,
    validate_job,
    validate_jobs,
)


def make_job(**overrides: Any) -> dict[str, Any]:
    job = {
        "external_id": "job-123",
        "title": "Data Analyst",
    }
    job.update(overrides)
    return job



def test_job_strips_whitespace():
    job = JobValidatedModel(
        **make_job(
            external_id="  job-123  ",
            title="  Data Analyst  ",
            company_name="  Acme  ",
        )
    )

    assert job.external_id == "job-123"
    assert job.title == "Data Analyst"
    assert job.company_name == "Acme"


def test_job_accepts_datetime_posted_date():
    posted = datetime(2026, 1, 15, 10, 30, tzinfo=timezone.utc)

    job = JobValidatedModel(**make_job(posted_date=posted))

    assert job.posted_date is posted


def test_job_parses_iso_posted_date():
    job = JobValidatedModel(
        **make_job(posted_date="2026-01-15T10:30:00")
    )

    assert job.posted_date == datetime(2026, 1, 15, 10, 30)


def test_job_parses_zulu_posted_date():
    job = JobValidatedModel(
        **make_job(posted_date="2026-01-15T10:30:00Z")
    )

    assert job.posted_date is not None
    assert job.posted_date.tzinfo is not None
    assert job.posted_date.isoformat() == "2026-01-15T10:30:00+00:00"

def test_job_allows_missing_posted_date():
    job = JobValidatedModel(**make_job())

    assert job.posted_date is None


def test_job_allows_explicit_none_posted_date():
    """Test posted_date validator accepts an explicit None value."""
    job = JobValidatedModel(**make_job(posted_date=None))

    assert job.posted_date is None


def test_job_rejects_invalid_date_type():
    with pytest.raises(ValidationError, match="Invalid date format"):
        JobValidatedModel(**make_job(posted_date=12345))


def test_job_rejects_salary_min_above_salary_max():
    with pytest.raises(
        ValidationError,
        match="salary_min \\(50000\\.0\\) cannot exceed salary_max \\(40000\\.0\\)",
    ):
        JobValidatedModel(
            **make_job(
                salary_min=50000,
                salary_max=40000,
            )
        )


def test_job_accepts_valid_salary_range():
    job = JobValidatedModel(
        **make_job(
            salary_min=40000,
            salary_max=50000,
        )
    )

    assert job.salary_min == 40000
    assert job.salary_max == 50000


def test_job_is_frozen():
    job = JobValidatedModel(**make_job())

    with pytest.raises(ValidationError):
        job.title = "Changed"


def test_validate_job_returns_validated_model():
    result = validate_job(
        make_job(
            title="  Data Analyst  ",
            salary_min=40000,
            salary_max=50000,
        )
    )

    assert isinstance(result, JobValidatedModel)
    assert result.title == "Data Analyst"
    assert result.salary_min == 40000


def test_validate_jobs_validates_all_jobs():
    jobs = [
        make_job(external_id="job-1", title="Data Analyst"),
        make_job(external_id="job-2", title="Data Engineer"),
    ]

    results = validate_jobs(jobs)

    assert len(results) == 2
    assert all(isinstance(job, JobValidatedModel) for job in results)
    assert [job.external_id for job in results] == ["job-1", "job-2"]


def test_validate_jobs_rejects_invalid_job():
    jobs = [
        make_job(external_id="job-1"),
        make_job(external_id="job-2", salary_min=50000, salary_max=40000),
    ]

    with pytest.raises(ValidationError):
        validate_jobs(jobs)
