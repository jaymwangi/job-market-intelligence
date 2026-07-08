"""
Unit tests for database health checks.
"""

from unittest.mock import MagicMock, patch

from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.database.health import check_database_connection, get_database_status


class TestDatabaseHealth:
    """Test suite for database health checks."""

    def test_check_database_connection_success(self):
        """Test successful database connection check."""
        mock_connection = MagicMock()
        mock_connection.execute.return_value = True

        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        with patch("app.database.health.engine", mock_engine):
            result = check_database_connection()

        assert result is True

        # Verify execute was called with SELECT 1
        mock_connection.execute.assert_called_once()
        sql = mock_connection.execute.call_args.args[0]
        assert str(sql) == "SELECT 1"

    def test_check_database_connection_operational_error(self):
        """Test database connection check with OperationalError."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = OperationalError(
            "BEGIN", {}, Exception("Connection failed")
        )

        with patch("app.database.health.engine", mock_engine):
            result = check_database_connection()
            assert result is False

    def test_check_database_connection_sqlalchemy_error(self):
        """Test database connection check with SQLAlchemyError."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = SQLAlchemyError("Database error")

        with patch("app.database.health.engine", mock_engine):
            result = check_database_connection()
            assert result is False

    def test_check_database_connection_generic_exception(self):
        """Test database connection check with generic exception."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = Exception("Unexpected error")

        with patch("app.database.health.engine", mock_engine):
            result = check_database_connection()
            assert result is False

    def test_get_database_status_success(self):
        """Test getting database status when healthy."""
        mock_connection = MagicMock()
        mock_connection.execute.side_effect = [
            MagicMock(scalar=lambda: "PostgreSQL 15.0 on x86_64"),
            MagicMock(scalar=lambda: "test_db"),
        ]

        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        with patch("app.database.health.engine", mock_engine):
            result = get_database_status()

            assert result["status"] == "healthy"
            assert "PostgreSQL" in result["version"]
            assert result["database"] == "test_db"

    def test_get_database_status_operational_error(self):
        """Test getting database status with OperationalError."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = OperationalError(
            "BEGIN", {}, Exception("Connection failed")
        )

        with patch("app.database.health.engine", mock_engine):
            result = get_database_status()

            assert result["status"] == "unhealthy"
            assert "Connection failed" in result["error"]
            assert "hint" in result

    def test_get_database_status_sqlalchemy_error(self):
        """Test getting database status with SQLAlchemyError."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = SQLAlchemyError("Database error")

        with patch("app.database.health.engine", mock_engine):
            result = get_database_status()

            assert result["status"] == "unhealthy"
            assert "Database error" in result["error"]
