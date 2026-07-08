"""
Unit tests for health check API routes.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.routes.health import check_database_connection
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
        mock_db.execute.return_value = True

        result = check_database_connection(mock_db)
        assert result is True
        mock_db.execute.assert_called_once()

    def test_check_database_connection_failure(self):
        """Test database connection check failure."""
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Connection failed")

        result = check_database_connection(mock_db)
        assert result is False

    def test_check_database_connection_exception(self):
        """Test database connection check with unexpected exception."""
        mock_db = Mock()
        mock_db.execute.side_effect = AttributeError("No such attribute")

        result = check_database_connection(mock_db)
        assert result is False

    def test_health_check_success(self, client, mocker):
        """Test successful health check."""
        mock_db = Mock()
        mocker.patch("app.api.routes.health.get_db", return_value=mock_db)
        mocker.patch("app.api.routes.health.check_database_connection", return_value=True)

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
        mocker.patch("app.api.routes.health.check_database_connection", return_value=False)

        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "disconnected"

    def test_health_check_environment(self, client, mocker):
        """Test health check returns correct environment."""
        mock_db = Mock()
        mocker.patch("app.api.routes.health.get_db", return_value=mock_db)
        mocker.patch("app.api.routes.health.check_database_connection", return_value=True)

        response = client.get("/api/v1/health")
        data = response.json()

        assert "environment" in data
        assert isinstance(data["environment"], str)

    def test_health_check_timestamp_format(self, client, mocker):
        """Test health check timestamp is in correct format."""
        mock_db = Mock()
        mocker.patch("app.api.routes.health.get_db", return_value=mock_db)
        mocker.patch("app.api.routes.health.check_database_connection", return_value=True)

        response = client.get("/api/v1/health")
        data = response.json()

        assert "timestamp" in data
        # Should be ISO format with Z suffix
        assert data["timestamp"].endswith("Z")

        # Should be parseable
        try:
            datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail("Timestamp is not in valid ISO format")

    def test_health_check_response_structure(self, client, mocker):
        """Test health check response has all required fields."""
        mock_db = Mock()
        mocker.patch("app.api.routes.health.get_db", return_value=mock_db)
        mocker.patch("app.api.routes.health.check_database_connection", return_value=True)

        response = client.get("/api/v1/health")
        data = response.json()

        expected_fields = {"status", "database", "environment", "timestamp"}
        assert set(data.keys()) == expected_fields
