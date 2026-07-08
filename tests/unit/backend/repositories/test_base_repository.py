"""
Unit tests for base repository.
"""

from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.repositories.base import BaseRepository


class TestBaseRepository:
    """Test suite for base repository operations."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_model(self):
        """Create a mock model class."""

        class MockModel:
            id = None
            name = None
            active = None

            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

        return MockModel

    @pytest.fixture
    def repository(self, mock_db, mock_model):
        """Create repository instance with mock db and model."""
        return BaseRepository(mock_model, mock_db)

    def test_init(self, repository, mock_db, mock_model):
        """Test repository initialization."""
        assert repository.db == mock_db
        assert repository.model == mock_model

    def test_build_query_no_filters(self, repository):
        """Test _build_query with no filters."""
        result = repository._build_query()
        repository.db.query.assert_called_once_with(repository.model)
        assert result == repository.db.query.return_value

    def test_build_query_with_filters(self, repository):
        """Test _build_query with filters."""
        result = repository._build_query(name="Test")

        repository.db.query.assert_called_once_with(repository.model)
        repository.db.query.return_value.filter.assert_called_once()
        assert result == repository.db.query.return_value.filter.return_value

    def test_create(self, repository):
        """Test creating a record."""
        mock_instance = Mock()
        repository.model = Mock(return_value=mock_instance)

        result = repository.create(name="Test", active=True)

        repository.model.assert_called_once_with(name="Test", active=True)
        repository.db.add.assert_called_once_with(mock_instance)
        repository.db.flush.assert_called_once()
        assert result == mock_instance

    def test_bulk_create(self, repository):
        """Test bulk creating records."""
        items = [{"name": "Item1"}, {"name": "Item2"}]

        result = repository.bulk_create(items)

        assert len(result) == 2
        repository.db.add_all.assert_called_once()
        repository.db.flush.assert_called_once()

    def test_get_found(self, repository):
        """Test get returns record when found."""
        mock_instance = Mock()
        mock_query = Mock()
        mock_query.first.return_value = mock_instance
        repository._build_query = Mock(return_value=mock_query)

        result = repository.get(id="123")

        assert result == mock_instance
        repository._build_query.assert_called_once_with(id="123")

    def test_get_not_found(self, repository):
        """Test get returns None when not found."""
        mock_query = Mock()
        mock_query.first.return_value = None
        repository._build_query = Mock(return_value=mock_query)

        result = repository.get(id="456")

        assert result is None
        repository._build_query.assert_called_once_with(id="456")

    def test_get_by_id_found(self, repository):
        """Test get_by_id returns record when found."""
        mock_instance = Mock()
        job_id = uuid4()
        mock_query = Mock()
        mock_query.first.return_value = mock_instance
        repository._build_query = Mock(return_value=mock_query)

        result = repository.get_by_id(job_id)

        assert result == mock_instance
        repository._build_query.assert_called_once_with(id=job_id)

    def test_get_by_id_not_found(self, repository):
        """Test get_by_id returns None when not found."""
        job_id = uuid4()
        mock_query = Mock()
        mock_query.first.return_value = None
        repository._build_query = Mock(return_value=mock_query)

        result = repository.get_by_id(job_id)

        assert result is None
        repository._build_query.assert_called_once_with(id=job_id)

    def test_find_all_no_filters(self, repository):
        """Test find_all with no filters."""
        mock_results = [Mock(), Mock()]
        mock_query = Mock()
        mock_query.all.return_value = mock_results
        repository._build_query = Mock(return_value=mock_query)

        result = repository.find_all()

        assert result == mock_results
        repository._build_query.assert_called_once()

    def test_find_all_with_order_by(self, repository):
        """Test find_all with order_by."""
        mock_results = [Mock(), Mock()]
        mock_query = Mock()
        mock_query.order_by.return_value.all.return_value = mock_results
        repository._build_query = Mock(return_value=mock_query)

        result = repository.find_all(order_by="name")

        assert result == mock_results
        repository._build_query.assert_called_once()

    def test_find_paginated(self, repository):
        """Test find_paginated with pagination."""
        mock_results = [Mock(), Mock()]
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_results
        repository._build_query = Mock(return_value=mock_query)

        result = repository.find_paginated(skip=10, limit=5)

        assert result == mock_results
        repository._build_query.assert_called_once()

    def test_update_found(self, repository):
        """Test update returns updated record when found."""
        mock_instance = Mock()
        job_id = uuid4()
        repository.get_by_id = Mock(return_value=mock_instance)

        result = repository.update(job_id, name="Updated")

        assert result == mock_instance
        repository.db.flush.assert_called_once()

    def test_update_not_found(self, repository):
        """Test update returns None when not found."""
        job_id = uuid4()
        repository.get_by_id = Mock(return_value=None)

        result = repository.update(job_id, name="Updated")

        assert result is None

    def test_delete_found(self, repository):
        """Test delete returns True when found."""
        mock_instance = Mock()
        job_id = uuid4()
        repository.get_by_id = Mock(return_value=mock_instance)

        result = repository.delete(job_id)

        assert result is True
        repository.db.delete.assert_called_once_with(mock_instance)
        repository.db.flush.assert_called_once()

    def test_delete_not_found(self, repository):
        """Test delete returns False when not found."""
        job_id = uuid4()
        repository.get_by_id = Mock(return_value=None)

        result = repository.delete(job_id)

        assert result is False

    def test_exists_true(self, repository):
        """Test exists returns True when record exists."""
        # The exists method does: self.db.query(self._build_query(**filters).exists()).scalar()
        # The simplest way to mock this is to mock db.query().scalar() directly
        # since that's the final call that returns the boolean
        repository.db.query.return_value.scalar.return_value = True

        result = repository.exists(id="123")

        assert result is True

    def test_exists_false(self, repository):
        """Test exists returns False when record not exists."""
        repository.db.query.return_value.scalar.return_value = False

        result = repository.exists(id="456")

        assert result is False

    def test_count(self, repository):
        """Test count returns number of records."""
        mock_query = Mock()
        mock_query.count.return_value = 10
        repository._build_query = Mock(return_value=mock_query)

        result = repository.count(active=True)

        assert result == 10
        repository._build_query.assert_called_once_with(active=True)
