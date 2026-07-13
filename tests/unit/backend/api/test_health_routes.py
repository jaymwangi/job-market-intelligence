"""
Unit tests for health check API routes.
"""

from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.health import check_database_connection_with_timing
from app.database.session import get_db
from app.main import app


class TestHealthRoutes:
    """Test suite for health check endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client without database dependency."""
        with TestClient(app) as test_client:
            yield test_client

    def test_check_database_connection_success(self):
        """Test successful database connection check."""
        mock_db = Mock()
        mock_log = MagicMock()
        mock_db.execute.return_value = True

        with patch("app.api.routes.health.check_db_health", return_value=True):
            is_healthy, response_ms = check_database_connection_with_timing(mock_db, mock_log)
            assert is_healthy is True
            assert response_ms >= 0

    def test_check_database_connection_failure(self):
        """Test database connection check failure."""
        mock_db = Mock()
        mock_log = MagicMock()
        mock_db.execute.side_effect = Exception("Connection failed")

        with patch("app.api.routes.health.check_db_health", return_value=False):
            is_healthy, response_ms = check_database_connection_with_timing(mock_db, mock_log)
            assert is_healthy is False
            assert response_ms < 1.0

    def test_check_database_connection_exception(self):
        """Test database connection check with unexpected exception."""
        mock_db = Mock()
        mock_log = MagicMock()
        mock_db.execute.side_effect = AttributeError("No such attribute")

        with patch("app.api.routes.health.check_db_health", side_effect=Exception("Unexpected error")):
            is_healthy, response_ms = check_database_connection_with_timing(mock_db, mock_log)
            assert is_healthy is False
            assert response_ms == 0
            mock_log.exception.assert_called_once()

    def test_health_check_success(self, client, mocker):
        """Test successful health check."""
        mock_db = Mock()
        mocker.patch("app.api.routes.health.get_db", return_value=mock_db)
        mocker.patch(
            "app.api.routes.health.check_database_connection_with_timing",
            return_value=(True, 10.5)
        )

        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "environment" in data
        assert "timestamp" in data

    def test_health_check_database_disconnected(self, client, mocker):
        """Test health check when database is disconnected."""
        mock_db = Mock()
        mocker.patch("app.api.routes.health.get_db", return_value=mock_db)
        mocker.patch(
            "app.api.routes.health.check_database_connection_with_timing",
            return_value=(False, 0)
        )

        response = client.get("/api/v1/health")
        assert response.status_code == 503

        data = response.json()
        assert "detail" in data
        assert data["detail"]["status"] == "unhealthy"
        assert data["detail"]["database"] == "disconnected"

    def test_health_check_environment(self, client, mocker):
        """Test health check returns correct environment."""
        mock_db = Mock()
        mocker.patch("app.api.routes.health.get_db", return_value=mock_db)
        mocker.patch(
            "app.api.routes.health.check_database_connection_with_timing",
            return_value=(True, 10.0)
        )

        response = client.get("/api/v1/health")
        data = response.json()

        assert "environment" in data
        assert isinstance(data["environment"], str)

    def test_health_check_timestamp_format(self, client, mocker):
        """Test health check timestamp is in correct format."""
        mock_db = Mock()
        mocker.patch("app.api.routes.health.get_db", return_value=mock_db)
        mocker.patch(
            "app.api.routes.health.check_database_connection_with_timing",
            return_value=(True, 10.0)
        )

        response = client.get("/api/v1/health")
        data = response.json()

        assert "timestamp" in data
        try:
            datetime.fromisoformat(data["timestamp"])
        except ValueError:
            pytest.fail(f"Timestamp is not in valid ISO format: {data['timestamp']}")

    def test_health_check_response_structure(self, client, mocker):
        """Test health check response has all required fields."""
        mock_db = Mock()
        mocker.patch("app.api.routes.health.get_db", return_value=mock_db)
        mocker.patch(
            "app.api.routes.health.check_database_connection_with_timing",
            return_value=(True, 10.0)
        )

        response = client.get("/api/v1/health")
        data = response.json()

        expected_fields = {
            "status", "database", "database_response_ms", 
            "environment", "version", "uptime_seconds", "timestamp"
        }
        assert set(data.keys()) == expected_fields

    def test_liveness_endpoint(self, client):
        """Test liveness endpoint."""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    def test_readiness_endpoint_success(self, client, mocker):
        """Test readiness endpoint when database is healthy."""
        mock_db = Mock()
        mocker.patch("app.api.routes.health.get_db", return_value=mock_db)
        mocker.patch(
            "app.api.routes.health.check_database_connection_with_timing",
            return_value=(True, 5.0)
        )

        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "environment" in data

    def test_readiness_endpoint_failure(self, client, mocker):
        """Test readiness endpoint when database is unhealthy."""
        mock_db = Mock()
        mocker.patch("app.api.routes.health.get_db", return_value=mock_db)
        mocker.patch(
            "app.api.routes.health.check_database_connection_with_timing",
            return_value=(False, 0)
        )

        response = client.get("/api/v1/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "not_ready"

    def test_database_health_endpoint_success(self, client, mocker):
        """Test database health endpoint when database is healthy."""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.server_time = datetime.now()
        mock_db.execute.return_value.first.return_value = mock_result
        mocker.patch("app.api.routes.health.get_db", return_value=mock_db)

        response = client.get("/api/v1/health/database")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "PostgreSQL"
        assert "response_time_ms" in data
        assert "connection_pool_size" in data

    def test_database_health_endpoint_failure(self, client):
        """Test database health endpoint when database is unhealthy using dependency_overrides."""
        # Create a mock session that raises an exception
        mock_db = Mock()
        mock_db.execute.side_effect = SQLAlchemyError("Database error")

        # Create the override function (sync generator, not async)
        def override_get_db():
            yield mock_db

        # Use dependency_overrides (the official FastAPI way)
        try:
            client.app.dependency_overrides[get_db] = override_get_db
            response = client.get("/api/v1/health/database")
        finally:
            # Clean up to avoid affecting other tests
            client.app.dependency_overrides.clear()

        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "unhealthy"
        assert data["detail"]["database"] == "PostgreSQL"