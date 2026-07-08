"""
Unit tests for backend job schemas.
"""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.job import JobFilters, JobListResponse, JobResponse


class TestJobResponse:
    """Test suite for JobResponse schema."""

    def test_valid_job_response(self):
        """Test creating a valid JobResponse."""
        job_id = uuid4()
        job = JobResponse(
            id=job_id,
            title="Python Developer",
            company_name="TechCorp",
            location="San Francisco",
            salary_min=100000.0,
            salary_max=150000.0,
            salary_currency="USD",
            posted_date=datetime.now(),
            source_site="LinkedIn",
            is_active=True,
        )
        assert job.id == job_id
        assert job.title == "Python Developer"
        assert job.company_name == "TechCorp"
        assert job.location == "San Francisco"
        assert job.salary_min == 100000.0
        assert job.salary_max == 150000.0
        assert job.salary_currency == "USD"
        assert job.is_active is True

    def test_job_response_optional_fields(self):
        """Test JobResponse with optional fields omitted."""
        job_id = uuid4()
        job = JobResponse(id=job_id, title="Python Developer")
        assert job.id == job_id
        assert job.title == "Python Developer"
        assert job.company_name is None
        assert job.location is None
        assert job.is_active is True  # Default value

    def test_job_response_invalid_uuid(self):
        """Test JobResponse with invalid UUID string."""
        # Pydantic will try to convert this string to UUID and fail
        with pytest.raises(ValidationError) as exc_info:
            JobResponse(id="invalid-uuid", title="Python Developer")  # type: ignore
        # Verify the error is about the UUID field
        assert "id" in str(exc_info.value)

    def test_job_response_negative_salary(self):
        """Test JobResponse with negative salary (no validation on salary_min)."""
        job_id = uuid4()
        # Pydantic doesn't validate salary_min > 0 unless we add a validator
        job = JobResponse(id=job_id, title="Python Developer", salary_min=-1000.0)
        assert job.salary_min == -1000.0  # It will accept negative values


class TestJobFilters:
    """Test suite for JobFilters schema."""

    def test_valid_job_filters(self):
        """Test creating valid JobFilters."""
        filters = JobFilters(
            company_name="TechCorp",
            location="San Francisco",
            source_site="LinkedIn",
            min_salary=100000.0,
            max_salary=150000.0,
        )
        assert filters.company_name == "TechCorp"
        assert filters.location == "San Francisco"
        assert filters.source_site == "LinkedIn"
        assert filters.min_salary == 100000.0
        assert filters.max_salary == 150000.0

    def test_job_filters_empty(self):
        """Test JobFilters with no filters."""
        filters = JobFilters()
        assert filters.company_name is None
        assert filters.location is None
        assert filters.source_site is None
        assert filters.min_salary is None
        assert filters.max_salary is None

    def test_job_filters_invalid_salary_range(self):
        """Test JobFilters with invalid salary range (no validation)."""
        # Pydantic doesn't validate min_salary < max_salary unless we add a validator
        filters = JobFilters(min_salary=200000.0, max_salary=100000.0)
        assert filters.min_salary == 200000.0
        assert filters.max_salary == 100000.0


class TestJobListResponse:
    """Test suite for JobListResponse schema."""

    @pytest.fixture
    def sample_job_data(self):
        """Create sample job data for testing."""
        return [
            JobResponse(id=uuid4(), title="Python Developer", company_name="TechCorp"),
            JobResponse(id=uuid4(), title="Data Engineer", company_name="DataInc"),
        ]

    def test_valid_job_list_response(self, sample_job_data):
        """Test creating a valid JobListResponse."""
        response = JobListResponse(page=1, limit=20, total=100, data=sample_job_data)
        assert response.page == 1
        assert response.limit == 20
        assert response.total == 100
        assert len(response.data) == 2
        assert response.data[0].title == "Python Developer"

    def test_job_list_response_invalid_page(self):
        """Test JobListResponse with invalid page (no validation)."""
        # Pydantic doesn't validate page > 0 unless we add a validator
        response = JobListResponse(page=0, limit=20, total=100, data=[])
        assert response.page == 0  # It will accept 0

    def test_job_list_response_invalid_limit(self):
        """Test JobListResponse with invalid limit (no validation)."""
        # Pydantic doesn't validate limit > 0 unless we add a validator
        response = JobListResponse(page=1, limit=0, total=100, data=[])
        assert response.limit == 0

    def test_job_list_response_limit_too_high(self):
        """Test JobListResponse with limit too high (no validation)."""
        # Pydantic doesn't validate limit <= 100 unless we add a validator
        response = JobListResponse(page=1, limit=200, total=100, data=[])
        assert response.limit == 200

    def test_job_list_response_negative_total(self):
        """Test JobListResponse with negative total (no validation)."""
        # Pydantic doesn't validate total >= 0 unless we add a validator
        response = JobListResponse(page=1, limit=20, total=-5, data=[])
        assert response.total == -5
