"""Unit tests for job repository."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.repositories.job_repository import JobRepository
from app.schemas.job import JobFilters


class TestJobRepository:
    """Test suite for current JobRepository contract."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance with mock database session."""
        return JobRepository(mock_db)

    @pytest.fixture
    def mock_job_validated(self):
        """Create a mock validated job matching JobValidated contract."""
        mock = Mock()
        mock.title = "Python Developer"
        mock.description = "Test description"
        mock.company = "TechCorp"
        mock.location = "San Francisco"
        mock.salary_min = 100000.0
        mock.salary_max = 150000.0
        mock.salary_currency = "USD"
        mock.source = "adzuna"
        mock.source_id = "job_123"
        mock.url = "https://example.com/job/123"
        mock.posted_date = datetime.now(UTC)

        # Enrichment fields
        mock.technology_category = "backend"
        mock.is_tech_role = True
        mock.country_code = "US"
        mock.employment_type = "full-time"
        mock.language = "en"

        return mock

    def test_init(self, repository, mock_db):
        """Test repository initialization."""
        assert repository.session == mock_db

    # ============================================================
    # ETL Methods
    # ============================================================

    def test_to_decimal_with_value(self, repository):
        """Test float values are converted to Decimal."""
        result = repository._to_decimal(100000.50)

        assert result is not None
        assert str(result) == "100000.5"

    def test_to_decimal_with_none(self, repository):
        """Test None remains None."""
        assert repository._to_decimal(None) is None

    def test_build_job_dict(self, repository, mock_job_validated):
        """Test JobValidated is mapped to database fields."""
        result = repository._build_job_dict(mock_job_validated)

        assert result["title"] == "Python Developer"
        assert result["description"] == "Test description"
        assert result["company_name"] == "TechCorp"
        assert result["location"] == "San Francisco"
        assert result["salary_min"] == 100000
        assert result["salary_max"] == 150000
        assert result["salary_currency"] == "USD"
        assert result["source_site"] == "adzuna"
        assert result["source_id"] == "job_123"
        assert result["source_url"] == "https://example.com/job/123"
        assert result["posted_date"] == mock_job_validated.posted_date

        assert result["technology_category"] == "backend"
        assert result["is_tech_role"] is True
        assert result["country_code"] == "US"
        assert result["employment_type"] == "full-time"
        assert result["language"] == "en"

        assert result["is_active"] is True
        assert result["is_deleted"] is False
        assert result["scraped_date"] is not None

    def test_upsert_from_validated(self, repository, mock_db, mock_job_validated):
        """Test single validated job upsert."""
        repository.upsert_from_validated(mock_job_validated)

        mock_db.execute.assert_called_once()

    def test_upsert_batch_from_validated_empty(self, repository, mock_db):
        """Test empty batch performs no database operation."""
        repository.upsert_batch_from_validated([])

        mock_db.execute.assert_not_called()

    def test_upsert_batch_from_validated(self, repository, mock_db, mock_job_validated):
        """Test batch validated job upsert."""
        repository.upsert_batch_from_validated(
            [mock_job_validated, mock_job_validated]
        )

        mock_db.execute.assert_called_once()

    def test_delete_jobs_older_than(self, repository, mock_db):
        """Test deletion of jobs older than cutoff date."""
        cutoff = datetime.now(UTC)

        (
            mock_db.query.return_value
            .filter.return_value
            .delete.return_value
        ) = 7

        result = repository.delete_jobs_older_than(cutoff)

        assert result == 7
        mock_db.query.assert_called_once()

    # ============================================================
    # Filter Methods
    # ============================================================

    def test_apply_filters_no_filters(self, repository):
        """Test apply_filters with no optional filters."""
        mock_query = Mock()

        # Every filter call should return the same query object so that
        # chained filters can be inspected reliably.
        mock_query.filter.return_value = mock_query

        filters = JobFilters()

        result = repository._apply_filters(mock_query, filters, None)

        assert result is mock_query
        mock_query.filter.assert_called_once()

    def test_apply_filters_with_company(self, repository):
        """Test company filter is applied."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query

        filters = JobFilters(company_name="TechCorp")

        result = repository._apply_filters(mock_query, filters, None)

        assert result is mock_query
        assert mock_query.filter.call_count == 2

    def test_apply_filters_with_location(self, repository):
        """Test location filter is applied."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query

        filters = JobFilters(location="San Francisco")

        result = repository._apply_filters(mock_query, filters, None)

        assert result is mock_query
        assert mock_query.filter.call_count == 2

    def test_apply_filters_with_search(self, repository):
        """Test search filter is applied."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query

        filters = JobFilters()

        result = repository._apply_filters(mock_query, filters, "Python")

        assert result is mock_query
        assert mock_query.filter.call_count == 2

    def test_apply_filters_with_salary_range(self, repository):
        """Test minimum and maximum salary filters are applied."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query

        filters = JobFilters(
            min_salary=100000.0,
            max_salary=150000.0,
        )

        result = repository._apply_filters(mock_query, filters, None)

        assert result is mock_query
        assert mock_query.filter.call_count == 3

    def test_apply_filters_with_all_filters(self, repository):
        """Test all supported filters can be applied together."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query

        filters = JobFilters(
            company_name="TechCorp",
            location="San Francisco",
            source_site="adzuna",
            min_salary=100000.0,
            max_salary=150000.0,
            country_code="us",
            technology_category="backend",
            employment_type="full-time",
            is_tech_role=True,
        )

        result = repository._apply_filters(mock_query, filters, "Python")

        assert result is mock_query
        assert mock_query.filter.call_count == 11

    # ============================================================
    # API Query Methods
    # ============================================================

    def test_get_jobs_empty(self, repository, mock_db):
        """Test get_jobs returns an empty list."""
        mock_query = Mock()
        mock_db.query.return_value = mock_query

        # Make query operations chain to the same mock.
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        filters = JobFilters()

        result = repository.get_jobs(filters, 0, 20, None)

        assert result == []
        mock_query.all.assert_called_once()

    def test_get_jobs_with_data(self, repository, mock_db):
        """Test get_jobs returns jobs."""
        mock_jobs = [Mock(), Mock()]

        mock_query = Mock()
        mock_db.query.return_value = mock_query

        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_jobs

        filters = JobFilters()

        result = repository.get_jobs(filters, 0, 20, None)

        assert result == mock_jobs
        assert len(result) == 2

    def test_count_jobs(self, repository, mock_db):
        """Test count_jobs returns count."""
        mock_query = Mock()
        mock_db.query.return_value = mock_query

        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10

        filters = JobFilters()

        result = repository.count_jobs(filters, None)

        assert result == 10
        mock_query.count.assert_called_once()

    def test_get_by_id_found(self, repository, mock_db):
        """Test get_by_id returns job when found."""
        mock_job = Mock()
        job_id = uuid4()

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_job

        result = repository.get_by_id(job_id)

        assert result == mock_job
        mock_query.first.assert_called_once()

    def test_get_by_id_not_found(self, repository, mock_db):
        """Test get_by_id returns None when not found."""
        job_id = uuid4()

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = repository.get_by_id(job_id)

        assert result is None

    # ============================================================
    # Analytics Methods
    # ============================================================

    def test_get_top_skills_empty(self, repository, mock_db):
        """Test get_top_skills returns an empty list."""
        mock_query = Mock()
        mock_db.query.return_value = mock_query

        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = repository.get_top_skills()

        assert result == []

    def test_get_country_distribution_empty(self, repository, mock_db):
        """Test country distribution returns an empty list."""
        mock_query = Mock()
        mock_db.query.return_value = mock_query

        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = repository.get_country_distribution()

        assert result == []

    def test_get_technology_distribution_empty(self, repository, mock_db):
        """Test technology distribution returns an empty list."""
        mock_query = Mock()
        mock_db.query.return_value = mock_query

        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = repository.get_technology_distribution()

        assert result == []

    def test_get_stats(self, repository, mock_db):
        """Test summary statistics."""
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [
            100,  # total jobs
            25,   # total companies
            5,    # total countries
            2,    # average minimum salary? No — see below
        ]

        # Configure the individual query chains explicitly because
        # get_stats performs several independent SQL queries.
        queries = []

        def query_side_effect(*args, **kwargs):
            query = Mock()
            query.filter.return_value = query
            query.scalar.return_value = 0
            queries.append(query)
            return query

        mock_db.query.side_effect = query_side_effect

        # Results in the exact order used by get_stats().
        scalar_results = iter(
            [
                100,       # total_jobs
                25,        # total_companies
                5,         # total_countries
                12,        # total_skills
                Decimal("75000"),  # average salary min
                Decimal("95000"),  # average salary max
                40,        # tech roles
            ]
        )

        def scalar_side_effect():
            return next(scalar_results)

        mock_db.query.side_effect = lambda *args, **kwargs: (
            lambda q: (
                setattr(q.scalar, "side_effect", scalar_side_effect) or q
            )
        )(Mock())

        # Rebuild with explicit query mocks so filter().scalar()
        # and direct scalar() both resolve correctly.
        query_mocks = []

        def make_query(*args, **kwargs):
            query = Mock()
            query.filter.return_value = query
            query.scalar.side_effect = scalar_side_effect
            query_mocks.append(query)
            return query

        mock_db.query.side_effect = make_query

        result = repository.get_stats()

        assert result["total_jobs"] == 100
        assert result["total_companies"] == 25
        assert result["total_countries"] == 5
        assert result["total_skills"] == 12
        assert result["average_salary_min"] == 75000.0
        assert result["average_salary_max"] == 95000.0
        assert result["tech_roles"] == 40

