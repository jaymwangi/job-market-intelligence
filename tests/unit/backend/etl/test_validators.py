"""
Unit tests for ETL validators.
"""

from datetime import datetime

import pytest
from pydantic import HttpUrl, ValidationError

from app.etl.validators.job_schema import JobValidated, validate_job, validate_jobs


class TestJobValidated:
    """Test suite for JobValidated model."""

    def test_valid_job_minimal(self):
        """Test creating a valid job with minimal fields."""
        job = JobValidated(
            external_id="12345", title="Python Developer", source="adzuna"
        )  # type: ignore
        assert job.external_id == "12345"
        assert job.title == "Python Developer"
        assert job.source == "adzuna"
        assert job.company_name is None
        assert job.salary_min is None
        assert job.salary_max is None

    def test_valid_job_full(self):
        """Test creating a valid job with all fields."""
        job = JobValidated(
            external_id="12345",
            title="Senior Python Developer",
            company_name="TechCorp",
            location="San Francisco, CA",
            description="We are looking for a skilled Python developer...",
            salary_min=120000.0,
            salary_max=180000.0,
            currency="USD",
            source="adzuna",
            source_url=HttpUrl("https://example.com/job/12345"),
            posted_date=datetime.fromisoformat("2026-01-15T10:30:00+00:00"),
        )  # type: ignore
        assert job.external_id == "12345"
        assert job.title == "Senior Python Developer"
        assert job.company_name == "TechCorp"
        assert job.location == "San Francisco, CA"
        assert job.salary_min == 120000.0
        assert job.salary_max == 180000.0
        assert job.currency == "USD"
        assert job.source == "adzuna"
        assert str(job.source_url) == "https://example.com/job/12345"
        assert isinstance(job.posted_date, datetime)

    def test_invalid_external_id_empty(self):
        """Test job with empty external_id."""
        with pytest.raises(ValidationError) as exc_info:
            JobValidated(external_id="", title="Python Developer", source="adzuna")  # type: ignore
        assert "external_id" in str(exc_info.value)

    def test_invalid_title_empty(self):
        """Test job with empty title."""
        with pytest.raises(ValidationError) as exc_info:
            JobValidated(external_id="12345", title="", source="adzuna")  # type: ignore
        assert "title" in str(exc_info.value)

    def test_invalid_salary_min_negative(self):
        """Test job with negative salary_min."""
        with pytest.raises(ValidationError) as exc_info:
            JobValidated(
                external_id="12345",
                title="Python Developer",
                source="adzuna",
                salary_min=-1000.0,
                salary_max=50000.0,
            )  # type: ignore
        assert "salary_min" in str(exc_info.value)

    def test_invalid_salary_max_negative(self):
        """Test job with negative salary_max."""
        with pytest.raises(ValidationError) as exc_info:
            JobValidated(
                external_id="12345",
                title="Python Developer",
                source="adzuna",
                salary_min=50000.0,
                salary_max=-1000.0,
            )  # type: ignore
        assert "salary_max" in str(exc_info.value)

    def test_invalid_salary_range(self):
        """Test job with salary_min > salary_max."""
        with pytest.raises(ValidationError) as exc_info:
            JobValidated(
                external_id="12345",
                title="Python Developer",
                source="adzuna",
                salary_min=180000.0,
                salary_max=120000.0,
            )  # type: ignore
        assert "salary_min" in str(exc_info.value)
        assert "salary_max" in str(exc_info.value)

    def test_invalid_currency_length(self):
        """Test job with invalid currency code length."""
        with pytest.raises(ValidationError) as exc_info:
            JobValidated(
                external_id="12345", title="Python Developer", source="adzuna", currency="US"
            )  # type: ignore
        assert "currency" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            JobValidated(
                external_id="12345", title="Python Developer", source="adzuna", currency="USDD"
            )  # type: ignore
        assert "currency" in str(exc_info.value)

    def test_invalid_source_empty(self):
        """Test job with empty source."""
        with pytest.raises(ValidationError) as exc_info:
            JobValidated(external_id="12345", title="Python Developer", source="")  # type: ignore
        assert "source" in str(exc_info.value)

    def test_invalid_source_url(self):
        """Test job with invalid source_url."""
        with pytest.raises(ValidationError) as exc_info:
            JobValidated(
                external_id="12345",
                title="Python Developer",
                source="adzuna",
                source_url="not-a-url",  # type: ignore
            )  # type: ignore
        assert "source_url" in str(exc_info.value)

    def test_date_parsing_iso_format(self):
        """Test date parsing from ISO format string."""
        job = JobValidated(
            external_id="12345",
            title="Python Developer",
            source="adzuna",
            posted_date=datetime.fromisoformat("2026-01-15T10:30:00+00:00"),
        )  # type: ignore
        assert isinstance(job.posted_date, datetime)
        assert job.posted_date.year == 2026
        assert job.posted_date.month == 1
        assert job.posted_date.day == 15

    def test_date_parsing_datetime_object(self):
        """Test date parsing from datetime object."""
        now = datetime.now()
        job = JobValidated(
            external_id="12345", title="Python Developer", source="adzuna", posted_date=now
        )  # type: ignore
        assert job.posted_date == now

    def test_date_parsing_none(self):
        """Test date parsing with None."""
        job = JobValidated(
            external_id="12345", title="Python Developer", source="adzuna", posted_date=None
        )  # type: ignore
        assert job.posted_date is None

    def test_model_config_frozen(self):
        """Test that model is frozen (immutable)."""
        job = JobValidated(
            external_id="12345", title="Python Developer", source="adzuna"
        )  # type: ignore
        with pytest.raises(Exception):
            job.title = "New Title"  # Should raise error because frozen=True

    def test_string_stripping(self):
        """Test that strings are stripped of whitespace."""
        job = JobValidated(
            external_id="  12345  ",
            title="  Python Developer  ",
            company_name="  TechCorp  ",
            source="adzuna",
        )  # type: ignore
        assert job.external_id == "12345"
        assert job.title == "Python Developer"
        assert job.company_name == "TechCorp"


class TestValidateJob:
    """Test suite for validate_job function."""

    def test_validate_job_success(self):
        """Test successful job validation."""
        job_dict = {
            "external_id": "12345",
            "title": "Python Developer",
            "company_name": "TechCorp",
            "salary_min": 100000.0,
            "salary_max": 150000.0,
            "currency": "USD",
            "source": "adzuna",
        }
        job = validate_job(job_dict)
        assert isinstance(job, JobValidated)
        assert job.external_id == "12345"
        assert job.title == "Python Developer"

    def test_validate_job_failure(self):
        """Test job validation failure."""
        job_dict = {"external_id": "", "title": "Python Developer", "source": "adzuna"}
        with pytest.raises(ValidationError):
            validate_job(job_dict)

    def test_validate_job_with_extra_fields(self):
        """Test validation with extra fields (should be ignored)."""
        job_dict = {
            "external_id": "12345",
            "title": "Python Developer",
            "source": "adzuna",
            "extra_field": "This should be ignored",
        }
        job = validate_job(job_dict)
        assert isinstance(job, JobValidated)
        assert not hasattr(job, "extra_field")


class TestValidateJobs:
    """Test suite for validate_jobs function."""

    def test_validate_jobs_success(self):
        """Test successful batch validation."""
        jobs = [
            {"external_id": "1", "title": "Job 1", "source": "adzuna"},
            {"external_id": "2", "title": "Job 2", "source": "adzuna"},
        ]
        validated = validate_jobs(jobs)
        assert len(validated) == 2
        assert all(isinstance(job, JobValidated) for job in validated)
        assert validated[0].external_id == "1"
        assert validated[1].external_id == "2"

    def test_validate_jobs_empty_list(self):
        """Test batch validation with empty list."""
        validated = validate_jobs([])
        assert validated == []

    def test_validate_jobs_failure(self):
        """Test batch validation with one invalid job."""
        jobs = [
            {"external_id": "1", "title": "Job 1", "source": "adzuna"},
            {"external_id": "", "title": "Job 2", "source": "adzuna"},
        ]
        with pytest.raises(ValidationError):
            validate_jobs(jobs)
