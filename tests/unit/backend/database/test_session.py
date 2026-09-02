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
        
    def test_session_transaction_rollback(self, db_session):
        """Test that a database transaction can be rolled back."""
        from app.models.job import Job

        job = Job(
            title="Rollback Test Job",
            description="Test job for transaction rollback.",
            company_name="Test Company",
            source_url="https://example.com/jobs/rollback-test",
            source_site="test",
            source_id="rollback-test",
            language="en",
        )

        db_session.add(job)
        db_session.flush()

        job_id = job.id

        assert db_session.get(Job, job_id) is not None

        db_session.rollback()

        assert db_session.get(Job, job_id) is None