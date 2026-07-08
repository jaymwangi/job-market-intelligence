"""
Unit tests for ETL transformers.
"""

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
            "salary": {"min": 100000, "max": 150000, "currency": "USD"},
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
                "salary": {"min": 130000, "max": 190000, "currency": "USD"},
                "redirect_url": "https://example.com/job/456",
                "created": "2026-01-16T10:30:00Z",
            },
        ]

    def test_transform_one(self, transformer, raw_job):
        """Test transforming a single job."""
        result = transformer.transform_one(raw_job)

        assert result["external_id"] == "job_123"
        assert result["title"] == "Senior Python Developer"
        assert result["company_name"] == "TechCorp Inc"
        assert result["location"] == "San Francisco, CA"
        assert result["description"] == "We are looking for a Python developer..."
        assert result["salary_min"] == 100000
        assert result["salary_max"] == 150000
        assert result["currency"] == "USD"
        assert result["source"] == "adzuna"
        assert result["source_url"] == "https://example.com/job/123"
        assert result["posted_date"] == "2026-01-15T10:30:00Z"

    def test_transform(self, transformer, raw_jobs):
        """Test transforming multiple jobs."""
        results = transformer.transform(raw_jobs)

        assert len(results) == 2
        assert results[0]["external_id"] == "job_123"
        assert results[0]["title"] == "Senior Python Developer"
        assert results[1]["external_id"] == "job_456"
        assert results[1]["title"] == "Data Engineer"

    def test_transform_empty(self, transformer):
        """Test transforming empty list."""
        results = transformer.transform([])
        assert results == []

    def test_company_extraction(self, transformer, raw_job):
        """Test company name extraction from nested structure."""
        result = transformer.transform_one(raw_job)
        assert result["company_name"] == "TechCorp Inc"

        # Test with company as string
        job_no_company = {"id": "1", "title": "Test", "company": "DirectCompany"}
        result = transformer.transform_one(job_no_company)
        assert result["company_name"] == "DirectCompany"

        # Test with no company
        job_no_company = {"id": "1", "title": "Test"}
        result = transformer.transform_one(job_no_company)
        assert result["company_name"] is None

    def test_location_extraction(self, transformer, raw_job):
        """Test location extraction from nested structure."""
        result = transformer.transform_one(raw_job)
        assert result["location"] == "San Francisco, CA"

        # Test with location as string
        job_no_location = {"id": "1", "title": "Test", "location": "Remote"}
        result = transformer.transform_one(job_no_location)
        assert result["location"] == "Remote"

        # Test with no location
        job_no_location = {"id": "1", "title": "Test"}
        result = transformer.transform_one(job_no_location)
        assert result["location"] is None

    def test_salary_extraction(self, transformer, raw_job):
        """Test salary extraction from nested structure."""
        result = transformer.transform_one(raw_job)
        assert result["salary_min"] == 100000
        assert result["salary_max"] == 150000

        # Test with no salary
        job_no_salary = {"id": "1", "title": "Test"}
        result = transformer.transform_one(job_no_salary)
        assert result["salary_min"] is None
        assert result["salary_max"] is None

    def test_currency_extraction(self, transformer, raw_job):
        """Test currency extraction from nested structure."""
        result = transformer.transform_one(raw_job)
        assert result["currency"] == "USD"

        # Test with currency in root
        job_currency = {"id": "1", "title": "Test", "salary_currency": "EUR"}
        result = transformer.transform_one(job_currency)
        assert result["currency"] == "EUR"

    def test_source_constant(self, transformer):
        """Test that source is always 'adzuna'."""
        job = {"id": "1", "title": "Test"}
        result = transformer.transform_one(job)
        assert result["source"] == "adzuna"

    def test_missing_fields(self, transformer):
        """Test transformation with missing fields."""
        job = {"id": "1"}
        result = transformer.transform_one(job)

        assert result["external_id"] == "1"
        assert result["title"] is None
        assert result["company_name"] is None
        assert result["location"] is None
        assert result["description"] is None
        assert result["salary_min"] is None
        assert result["salary_max"] is None
        assert result["currency"] is None
        assert result["source"] == "adzuna"
        assert result["source_url"] is None
        assert result["posted_date"] is None
