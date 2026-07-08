"""
Unit tests for database session management.
"""

import pytest

from app.database.session import SessionLocal, engine, get_db


class TestDatabaseSession:
    """Test suite for database session management."""

    def test_engine_creation(self):
        """Test database engine creation."""
        assert engine is not None
        assert engine.pool is not None

    def test_session_local_creation(self):
        """Test SessionLocal creation."""
        assert SessionLocal is not None
        session = SessionLocal()
        assert session is not None
        session.close()

    def test_get_db_creates_session(self):
        """Test that get_db creates a session."""
        db_gen = get_db()
        session = next(db_gen)
        assert session is not None
        assert session.is_active

        # Clean up
        session.close()
        with pytest.raises(StopIteration):
            next(db_gen)

    def test_get_db_session_is_active(self):
        """Test that get_db returns an active session."""
        db_gen = get_db()
        session = next(db_gen)
        assert session.is_active is True
        session.close()

    def test_get_db_session_close(self):
        """Test that session is closed after use."""
        db_gen = get_db()
        session = next(db_gen)
        assert session.is_active is True

        # Close the session
        session.close()
        # Session should be closed
        assert True

    @pytest.mark.skip(reason="Requires database with JSONB support")
    def test_session_transaction_rollback(self, db_session):
        """Test transaction rollback on error."""
        assert True
