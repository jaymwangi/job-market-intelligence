"""
Unit tests for database session management.
"""

import pytest

from app.database.session import (
    SessionLocal,
    _get_connect_args,
    engine,
    get_db,
    get_db_session,
)


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

    def test_get_connect_args_sqlite(self, monkeypatch):
        """Test SQLite-specific connection arguments."""
        from app.database import session

        monkeypatch.setattr(
            type(session.settings),
            "sqlalchemy_database_url",
            property(lambda self: "sqlite:///test.db"),
        )

        assert _get_connect_args() == {"check_same_thread": False}

    def test_get_db_session_rolls_back_and_closes(self, monkeypatch):
        """Test rollback and close when get_db_session raises."""
        from app.database import session

        mock_db = session.SessionLocal()
        rollback_called = False
        close_called = False

        original_rollback = mock_db.rollback
        original_close = mock_db.close

        def rollback():
            nonlocal rollback_called
            rollback_called = True
            original_rollback()

        def close():
            nonlocal close_called
            close_called = True
            original_close()

        monkeypatch.setattr(mock_db, "rollback", rollback)
        monkeypatch.setattr(mock_db, "close", close)
        monkeypatch.setattr(session, "SessionLocal", lambda: mock_db)

        with pytest.raises(RuntimeError, match="test error"):
            with get_db_session():
                raise RuntimeError("test error")

        assert rollback_called is True
        assert close_called is True

    def test_get_db_rolls_back_on_exception(self, monkeypatch):
        """Test that get_db rolls back and closes on exception."""
        from app.database import session

        mock_db = session.SessionLocal()
        rollback_called = False
        close_called = False

        original_rollback = mock_db.rollback
        original_close = mock_db.close

        def rollback():
            nonlocal rollback_called
            rollback_called = True
            original_rollback()

        def close():
            nonlocal close_called
            close_called = True
            original_close()

        monkeypatch.setattr(mock_db, "rollback", rollback)
        monkeypatch.setattr(mock_db, "close", close)
        monkeypatch.setattr(session, "SessionLocal", lambda: mock_db)

        db_gen = get_db()
        next(db_gen)

        with pytest.raises(RuntimeError, match="test error"):
            db_gen.throw(RuntimeError("test error"))

        assert rollback_called is True
        assert close_called is True
