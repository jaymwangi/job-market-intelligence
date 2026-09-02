"""
Unit tests for ETL validators.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.etl.schemas.enriched import JobEnriched
from app.etl.schemas.validated import JobValidated
from app.etl.validators.job_schema import JobValidator


def make_enriched_job(**overrides) -> JobEnriched:
    """Create a valid JobEnriched fixture for validator tests."""
    data = {
        "source_id": "12345",
        "source": "adzuna",
        "title": "Python Developer",
        "company": "TechCorp",
        "location": "Nairobi, Kenya",
        "description": "Python developer role.",
        "salary_min": 100000.0,
        "salary_max": 150000.0,
        "salary_currency": "USD",
        "employment_type": "FULL_TIME",
        "category": "IT",
        "posted_date": datetime(2026, 1, 15, 10, 30, tzinfo=UTC),
        "scraped_date": datetime(2026, 1, 15, 12, 30, tzinfo=UTC),
        "url": "https://example.com/job/12345",
        "language": "en",
        "skills": ["Python", "PostgreSQL"],
        "technology_category": "backend",
        "is_tech_role": True,
        "tech_confidence": 0.92,
        "matched_tech_terms": ["Python", "Django"],
        "country_code": "KE",
        "currency": "USD",
        "normalized_salary_min": 100000.0,
        "normalized_salary_max": 150000.0,
    }
    data.update(overrides)
    return JobEnriched(**data)


class TestJobValidated:
    """Test suite for JobValidated model."""

    def test_valid_job_minimal(self):
        """Test creating a valid JobValidated job."""
        job = JobValidated(
            source_id="12345",
            title="Python Developer",
            company="TechCorp",
            location="Nairobi, Kenya",
        )

        assert job.source_id == "12345"
        assert job.title == "Python Developer"
        assert job.company == "TechCorp"
        assert job.location == "Nairobi, Kenya"
        assert job.source == "adzuna"
        assert job.salary_min is None
        assert job.salary_max is None
        assert job.is_tech_role is False

    def test_valid_job_full(self):
        """Test creating a fully populated valid job."""
        job = make_enriched_job(
            source_id="12345",
            title="Senior Python Developer",
            company="TechCorp",
            salary_min=120000.0,
            salary_max=180000.0,
            currency="USD",
        )

        validated = JobValidated(
            **job.model_dump(),
            validation_timestamp=datetime.now(UTC),
            validation_warnings=[],
        )

        assert validated.source_id == "12345"
        assert validated.title == "Senior Python Developer"
        assert validated.company == "TechCorp"
        assert validated.salary_min == 120000.0
        assert validated.salary_max == 180000.0
        assert validated.currency == "USD"
        assert isinstance(validated.validation_timestamp, datetime)
        assert validated.validation_warnings == []

    def test_invalid_currency_length(self):
        """Test that invalid currency codes are rejected."""
        with pytest.raises(ValidationError):
            make_enriched_job(currency="US")

        with pytest.raises(ValidationError):
            make_enriched_job(currency="USDD")

    def test_invalid_country_code_length(self):
        """Test that invalid country codes are rejected."""
        with pytest.raises(ValidationError):
            make_enriched_job(country_code="USA")

    def test_invalid_technology_confidence(self):
        """Test that technology confidence outside 0-1 is rejected."""
        with pytest.raises(ValidationError):
            make_enriched_job(tech_confidence=1.5)

        with pytest.raises(ValidationError):
            make_enriched_job(tech_confidence=-0.1)

    def test_tech_role_requires_category(self):
        """Test that tech roles require a technology category."""
        with pytest.raises(ValidationError):
            make_enriched_job(
                is_tech_role=True,
                technology_category=None,
            )

    def test_tech_role_requires_confidence(self):
        """Test that tech roles require tech confidence."""
        with pytest.raises(ValidationError):
            make_enriched_job(
                is_tech_role=True,
                tech_confidence=None,
            )

    def test_non_tech_role_rejects_category(self):
        """Test that non-tech roles cannot have a technology category."""
        with pytest.raises(ValidationError):
            make_enriched_job(
                is_tech_role=False,
                technology_category="backend",
                tech_confidence=None,
                matched_tech_terms=[],
            )

    def test_non_tech_role_rejects_confidence(self):
        """Test that non-tech roles cannot have tech confidence."""
        with pytest.raises(ValidationError):
            make_enriched_job(
                is_tech_role=False,
                technology_category=None,
                tech_confidence=0.8,
                matched_tech_terms=[],
            )

    def test_string_normalization(self):
        """Test that supported string fields are normalized."""
        job = make_enriched_job(
            title="  Python Developer  ",
            company="  TechCorp  ",
            language="EN",
            country_code="ke",
            currency="usd",
        )

        assert job.title == "Python Developer"
        assert job.company == "TechCorp"
        assert job.language == "en"
        assert job.country_code == "KE"
        assert job.currency == "USD"


class TestJobValidator:
    """Test suite for JobValidator."""

    def test_validate_success(self):
        """Test successful validation of an enriched job."""
        validator = JobValidator()
        job = make_enriched_job()

        validated = validator.validate(job)

        assert isinstance(validated, JobValidated)
        assert validated.source_id == "12345"
        assert validated.title == "Python Developer"
        assert validated.company == "TechCorp"
        assert validated.validation_warnings == []

    def test_validate_missing_source_id(self):
        """Test that a job missing source_id is rejected."""
        validator = JobValidator()
        job = make_enriched_job(source_id="")

        validated = validator.validate(job)

        assert validated is None

    def test_validate_missing_title(self):
        """Test that a job missing title is rejected."""
        validator = JobValidator()
        job = make_enriched_job(title="")

        validated = validator.validate(job)

        assert validated is None

    def test_validate_missing_company(self):
        """Test that a job missing company is rejected."""
        validator = JobValidator()
        job = make_enriched_job(company="")

        validated = validator.validate(job)

        assert validated is None

    def test_validate_negative_salary_min(self):
        """Test that negative salary_min is rejected."""
        validator = JobValidator()
        job = make_enriched_job(salary_min=-1000.0)

        validated = validator.validate(job)

        assert validated is None

    def test_validate_negative_salary_max(self):
        """Test that negative salary_max is rejected."""
        validator = JobValidator()
        job = make_enriched_job(salary_max=-1000.0)

        validated = validator.validate(job)

        assert validated is None

    def test_validate_swaps_reversed_salary_range(self):
        """Test that reversed salary ranges are swapped with a warning."""
        validator = JobValidator()
        job = make_enriched_job(
            salary_min=180000.0,
            salary_max=120000.0,
        )

        validated = validator.validate(job)

        assert validated is not None
        assert validated.salary_min == 120000.0
        assert validated.salary_max == 180000.0
        assert "Min salary > max salary - values swapped" in (
            validated.validation_warnings
        )

    def test_validate_sets_scraped_date_when_missing(self):
        """Test that missing scraped_date receives a timestamp."""
        validator = JobValidator()
        job = make_enriched_job(scraped_date=None)

        validated = validator.validate(job)

        assert validated is not None
        assert validated.scraped_date is not None
        assert isinstance(validated.scraped_date, datetime)

    def test_validate_batch_success(self):
        """Test successful batch validation."""
        validator = JobValidator()

        jobs = [
            make_enriched_job(source_id="1", title="Job 1"),
            make_enriched_job(source_id="2", title="Job 2"),
        ]

        validated = validator.validate_batch(jobs)

        assert len(validated) == 2
        assert all(isinstance(job, JobValidated) for job in validated)
        assert validated[0].source_id == "1"
        assert validated[1].source_id == "2"

    def test_validate_batch_empty(self):
        """Test validation of an empty batch."""
        validator = JobValidator()

        validated = validator.validate_batch([])

        assert validated == []

    def test_validate_batch_drops_invalid_jobs(self):
        """Test that invalid jobs are dropped from the batch."""
        validator = JobValidator()

        jobs = [
            make_enriched_job(source_id="1", title="Job 1"),
            make_enriched_job(source_id="", title="Job 2"),
            make_enriched_job(source_id="3", title="Job 3"),
        ]

        validated = validator.validate_batch(jobs)

        assert len(validated) == 2
        assert [job.source_id for job in validated] == ["1", "3"]