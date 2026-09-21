"""
Unit tests for database health check functions.
"""

from unittest.mock import MagicMock, patch

from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.database.health import (
    check_database_connection,
    check_database_health,
    get_database_status,
)


class TestDatabaseHealth:
    """Tests for database health check functions."""

    def test_check_database_connection_success(self):
        """Test successful database connection check."""
        mock_connection = MagicMock()
        mock_connection.execute.return_value = True

        with patch("app.database.health.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_connection
            mock_session_local.return_value = mock_session

            # No parameters needed - function now handles optional params
            is_healthy = check_database_connection()

            assert is_healthy is True
            mock_connection.execute.assert_called_once()

    def test_check_database_connection_operational_error(self):
        """Test database connection check with OperationalError."""
        with patch("app.database.health.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.__enter__.side_effect = OperationalError(
                "BEGIN", {}, Exception("Connection failed")
            )
            mock_session_local.return_value = mock_session

            is_healthy = check_database_connection()
            assert is_healthy is False

    def test_check_database_connection_sqlalchemy_error(self):
        """Test database connection check with SQLAlchemyError."""
        with patch("app.database.health.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.__enter__.side_effect = SQLAlchemyError("Database error")
            mock_session_local.return_value = mock_session

            is_healthy = check_database_connection()
            assert is_healthy is False

    def test_check_database_connection_generic_exception(self):
        """Test database connection check with generic exception."""
        with patch("app.database.health.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.__enter__.side_effect = Exception("Unexpected error")
            mock_session_local.return_value = mock_session

            is_healthy = check_database_connection()
            assert is_healthy is False

    def test_get_database_status_success(self):
        """Test getting database status when healthy."""
        mock_connection = MagicMock()
        mock_connection.execute.side_effect = [
            MagicMock(scalar=lambda: "PostgreSQL 15.0 on x86_64"),
            MagicMock(scalar=lambda: "test_db"),
        ]

        with patch("app.database.health.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_connection
            mock_session_local.return_value = mock_session

            status = get_database_status()

            assert status["status"] == "healthy"
            assert "version" in status
            assert "database" in status
            assert status["version"] == "PostgreSQL 15.0 on x86_64"
            assert status["database"] == "test_db"

    def test_get_database_status_operational_error(self):
        """Test getting database status with OperationalError."""
        with patch("app.database.health.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.__enter__.side_effect = OperationalError(
                "BEGIN", {}, Exception("Connection failed")
            )
            mock_session_local.return_value = mock_session

            status = get_database_status()

            assert status["status"] == "unhealthy"
            assert "error" in status
            assert "Connection failed" in status["error"]

    def test_get_database_status_sqlalchemy_error(self):
        """Test getting database status with SQLAlchemyError."""
        with patch("app.database.health.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.__enter__.side_effect = SQLAlchemyError("Database error")
            mock_session_local.return_value = mock_session

            status = get_database_status()

            assert status["status"] == "unhealthy"
            assert "error" in status
            assert "Database error" in status["error"]

    def test_check_database_connection_operational_error_with_custom_log(self):
        """Test OperationalError with a custom logger."""
        mock_db = MagicMock()
        mock_db.execute.side_effect = OperationalError(
            "SELECT 1", {}, Exception("Connection failed")
        )
        mock_log = MagicMock()

        result = check_database_connection(db=mock_db, log=mock_log)

        assert result is False
        mock_log.error.assert_called_once()
        assert mock_log.error.call_args.args[0] == (
            "Operational error connecting to database"
        )

    def test_check_database_connection_sqlalchemy_error_with_custom_log(self):
        """Test SQLAlchemyError with a custom logger."""
        mock_db = MagicMock()
        mock_db.execute.side_effect = SQLAlchemyError("Database error")
        mock_log = MagicMock()

        result = check_database_connection(db=mock_db, log=mock_log)

        assert result is False
        mock_log.error.assert_called_once()
        assert mock_log.error.call_args.args[0] == (
            "SQLAlchemy error connecting to database"
        )

    def test_check_database_connection_generic_exception_with_custom_log(self):
        """Test generic exception with a custom logger."""
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("Unexpected error")
        mock_log = MagicMock()

        result = check_database_connection(db=mock_db, log=mock_log)

        assert result is False
        mock_log.error.assert_called_once()
        assert mock_log.error.call_args.args[0] == (
            "Unexpected error connecting to database"
        )

    def test_check_database_health_success(self):
        """Test successful database health check."""
        mock_db = MagicMock()
        mock_db.execute.return_value = True

        result = check_database_health(db=mock_db)

        assert result == {"healthy": True, "status": "ok"}
        mock_db.execute.assert_called_once()

    def test_check_database_health_error(self):
        """Test database health check when an exception occurs."""
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("Database unavailable")

        result = check_database_health(db=mock_db)

        assert result == {
            "healthy": False,
            "status": "error",
            "message": "Database unavailable",
        }

    def test_get_database_status_sqlite_fallbacks(self):
        """Test SQLite fallbacks when PostgreSQL queries fail."""
        mock_connection = MagicMock()
        mock_connection.execute.side_effect = [
            Exception("No version()"),
            MagicMock(scalar=lambda: "3.45.0"),
            Exception("No current_database()"),
        ]

        with patch("app.database.health.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_connection
            mock_session_local.return_value = mock_session

            status = get_database_status()

        assert status == {
            "status": "healthy",
            "version": "SQLite 3.45.0",
            "database": "SQLite",
        }

    def test_check_database_health_success_without_db(self):
        """Test successful database health check using SessionLocal."""
        mock_connection = MagicMock()
        mock_connection.execute.return_value = True

        with patch("app.database.health.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_connection
            mock_session_local.return_value = mock_session

            result = check_database_health()

        assert result == {"healthy": True, "status": "ok"}
        mock_connection.execute.assert_called_once()