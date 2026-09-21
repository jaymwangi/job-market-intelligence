"""
Unit tests for ETL transformers.
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from app.etl.transformers.jobs_transformer import JobsTransformer


class TestJobsTransformer:
    """Test suite for JobsTransformer."""

    @pytest.fixture
    def transformer(self):
        """Create a JobsTransformer instance."""
        return JobsTransformer()

    @pytest.fixture
    def raw_job(self):
        """Sample raw job from Adzuna API."""
        return {
            "id": "job_123",
            "title": "Senior Python Developer",
            "company": {"display_name": "TechCorp Inc"},
            "location": {"display_name": "San Francisco, CA"},
            "description": "We are looking for a Python developer...",
            "salary": {
                "min": 100000,
                "max": 150000,
                "currency": "USD",
            },
            "redirect_url": "https://example.com/job/123",
            "created": "2026-01-15T10:30:00Z",
        }

    @pytest.fixture
    def raw_jobs(self, raw_job):
        """List of raw jobs."""
        return [
            raw_job,
            {
                "id": "job_456",
                "title": "Data Engineer",
                "company": {"display_name": "DataInc"},
                "location": {"display_name": "New York, NY"},
                "description": "Build data pipelines...",
                "salary": {
                    "min": 130000,
                    "max": 190000,
                    "currency": "USD",
                },
                "redirect_url": "https://example.com/job/456",
                "created": "2026-01-16T10:30:00Z",
            },
        ]

    def test_transform_one(self, transformer, raw_job):
        """Test transforming a single job."""
        result = transformer.transform_one(raw_job)

        assert result.source_id == "job_123"
        assert result.title == "Senior Python Developer"
        assert result.company == "TechCorp Inc"
        assert result.location == "San Francisco, CA"
        assert result.description == "We are looking for a Python developer..."
        assert result.salary_min == 100000
        assert result.salary_max == 150000
        assert result.salary_currency == "USD"
        assert result.source == "adzuna"
        assert str(result.url) == "https://example.com/job/123"
        assert result.posted_date == datetime.fromisoformat("2026-01-15T10:30:00+00:00")

    def test_transform(self, transformer, raw_jobs):
        """Test transforming multiple jobs."""
        results = transformer.transform(raw_jobs)

        assert len(results) == 2
        assert results[0].source_id == "job_123"
        assert results[0].title == "Senior Python Developer"
        assert results[1].source_id == "job_456"
        assert results[1].title == "Data Engineer"

    def test_transform_empty(self, transformer):
        """Test transforming empty list."""
        results = transformer.transform([])

        assert results == []

    def test_company_extraction(self, transformer, raw_job):
        """Test company name extraction from nested structure."""
        result = transformer.transform_one(raw_job)
        assert result.company == "TechCorp Inc"

        # Test with company as string
        job_with_string_company = {
            "id": "1",
            "title": "Test",
            "company": "DirectCompany",
        }
        result = transformer.transform_one(job_with_string_company)
        assert result.company == "DirectCompany"

        # Test with no company
        job_no_company = {
            "id": "1",
            "title": "Test",
        }
        result = transformer.transform_one(job_no_company)
        assert result.company == "Unknown"

    def test_location_extraction(self, transformer, raw_job):
        """Test location extraction from nested structure."""
        result = transformer.transform_one(raw_job)
        assert result.location == "San Francisco, CA"

        # Test with location as string
        job_with_string_location = {
            "id": "1",
            "title": "Test",
            "location": "Remote",
        }
        result = transformer.transform_one(job_with_string_location)
        assert result.location == "Remote"

        # Test with no location
        job_no_location = {
            "id": "1",
            "title": "Test",
        }
        result = transformer.transform_one(job_no_location)
        assert result.location == ""

    def test_salary_extraction(self, transformer, raw_job):
        """Test salary extraction from nested structure."""
        result = transformer.transform_one(raw_job)

        assert result.salary_min == 100000
        assert result.salary_max == 150000

        # Test with no salary
        job_no_salary = {
            "id": "1",
            "title": "Test",
        }
        result = transformer.transform_one(job_no_salary)

        assert result.salary_min is None
        assert result.salary_max is None

    def test_currency_extraction(self, transformer, raw_job):
        """Test currency extraction from nested structure."""
        result = transformer.transform_one(raw_job)

        assert result.salary_currency == "USD"

        # Test with currency in root
        job_currency = {
            "id": "1",
            "title": "Test",
            "salary_currency": "EUR",
        }
        result = transformer.transform_one(job_currency)

        assert result.salary_currency == "EUR"

    def test_source_constant(self, transformer):
        """Test that source is always 'adzuna'."""
        job = {
            "id": "1",
            "title": "Test",
        }

        result = transformer.transform_one(job)

        assert result.source == "adzuna"

    def test_missing_fields(self, transformer):
        """Test transformation with missing fields."""
        job = {"id": "1"}

        result = transformer.transform_one(job)

        assert result.source_id == "1"
        assert result.title == ""
        assert result.company == "Unknown"
        assert result.location == ""
        assert result.description == ""
        assert result.salary_min is None
        assert result.salary_max is None
        assert result.salary_currency is None
        assert result.source == "adzuna"
        assert result.url == ""
        assert result.posted_date is None

    def test_non_dict_category(self, transformer):
        """Test category extraction when category is not a dict."""
        job = {
            "id": "1",
            "title": "Test",
            "category": "Engineering",
        }

        result = transformer.transform_one(job)

        assert result.category == "Engineering"

    def test_transform_one_handles_exception(self, transformer):
        """Return None when an unexpected transformation error occurs."""
        job = {
            "id": "broken",
            "title": "Test",
        }

        with patch.object(
            transformer,
            "_company",
            side_effect=RuntimeError("test failure"),
        ):
            result = transformer.transform_one(job)

        assert result is None

    def test_parse_datetime_with_datetime(self, transformer):
        """Return datetime unchanged when input is already a datetime."""
        value = datetime.now(UTC)

        result = transformer._parse_datetime(value)

        assert result is value

    def test_parse_datetime_invalid_string(self, transformer):
        """Return None for an invalid datetime string."""
        result = transformer._parse_datetime("not-a-date")

        assert result is None

    def test_parse_datetime_unsupported_type(self, transformer):
        """Return None for unsupported datetime input types."""
        result = transformer._parse_datetime(12345)

        assert result is None

    def test_to_float_none(self, transformer):
        """Return None when converting None."""
        assert transformer._to_float(None) is None

    def test_to_float_invalid_value(self, transformer):
        """Return None when a value cannot be converted to float."""
        result = transformer._to_float("not-a-number")

        assert result is None

    def test_salary_extraction_from_top_level_field(self, transformer):
        """Use top-level salary fields when nested salary data is absent."""
        job = {
            "salary_min": "75000",
            "salary_max": "100000",
        }

        assert transformer._salary(job, "min") == 75000.0
        assert transformer._salary(job, "max") == 100000.0

    def test_parse_employment_type_matching_keyword(self, transformer):
        """Return the mapped employment type when a keyword matches."""
        assert transformer._parse_employment_type(
            {"contract_type": "full-time"}
        ) == "FULL_TIME"