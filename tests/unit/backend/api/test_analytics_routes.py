"""
Unit tests for analytics API routes.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.routes.analytics import get_service
from app.main import app


class TestAnalyticsRoutes:
    """Test suite for analytics endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client without database dependency."""
        with TestClient(app) as test_client:
            yield test_client

    @pytest.fixture
    def sample_analytics_response(self):
        """Sample analytics data for mocking."""
        return {
            "total_jobs": 1000,
            "recent_jobs_count": 50,
            "top_companies": [{"company": "TechCorp", "job_count": 120, "percentage": 12.0}],
            "top_locations": [{"location": "San Francisco", "job_count": 200, "percentage": 20.0}],
            "top_skills": [{"skill": "Python", "count": 450, "percentage": 25.0}],
            "salary_statistics": {
                "average": 135000.0,
                "minimum": 100000.0,
                "maximum": 180000.0,
                "median": 130000.0,
                "sample_size": 500,
                "currency": "USD",
            },
            "employment_types": [
                {"employment_type": "Full-time", "count": 800, "percentage": 80.0}
            ],
            "posting_trend": [{"date": "2026-01-15", "count": 45, "cumulative": 45}],
        }

    def test_get_top_skills(self, client, sample_analytics_response):
        """Test getting top skills."""
        mock_service = Mock()
        mock_service.get_top_skills.return_value = sample_analytics_response["top_skills"]

        # Override the dependency
        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/top-skills?limit=10")
            assert response.status_code == 200

            data = response.json()
            assert len(data) > 0
            assert "skill" in data[0]
            assert "count" in data[0]
            assert "percentage" in data[0]
        finally:
            app.dependency_overrides.clear()

    def test_get_top_skills_with_limit(self, client):
        """Test getting top skills with custom limit."""
        mock_skills = [
            {"skill": f"Skill {i}", "count": 100 - i * 10, "percentage": 10.0} for i in range(5)
        ]
        mock_service = Mock()
        mock_service.get_top_skills.return_value = mock_skills

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/top-skills?limit=5")
            data = response.json()
            assert len(data) == 5
        finally:
            app.dependency_overrides.clear()

    def test_get_top_companies(self, client, sample_analytics_response):
        """Test getting top companies."""
        mock_service = Mock()
        mock_service.get_top_companies.return_value = sample_analytics_response["top_companies"]

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/top-companies?limit=10")
            assert response.status_code == 200

            data = response.json()
            assert len(data) > 0
            assert "company" in data[0]
            assert "job_count" in data[0]
        finally:
            app.dependency_overrides.clear()

    def test_get_jobs_by_location(self, client, sample_analytics_response):
        """Test getting jobs by location."""
        mock_service = Mock()
        mock_service.get_jobs_by_location.return_value = sample_analytics_response["top_locations"]

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/jobs-by-location?limit=10")
            assert response.status_code == 200

            data = response.json()
            assert len(data) > 0
            assert "location" in data[0]
            assert "job_count" in data[0]
        finally:
            app.dependency_overrides.clear()

    def test_get_salary_statistics(self, client, sample_analytics_response):
        """Test getting salary statistics."""
        mock_service = Mock()
        mock_service.get_salary_statistics.return_value = sample_analytics_response[
            "salary_statistics"
        ]

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/salary-statistics")
            assert response.status_code == 200

            data = response.json()
            assert "average" in data
            assert "minimum" in data
            assert "maximum" in data
            assert "sample_size" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_employment_types(self, client, sample_analytics_response):
        """Test getting employment type distribution."""
        mock_service = Mock()
        mock_service.get_employment_types.return_value = sample_analytics_response[
            "employment_types"
        ]

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/employment-types")
            assert response.status_code == 200

            data = response.json()
            assert len(data) > 0
            assert "employment_type" in data[0]
            assert "count" in data[0]
        finally:
            app.dependency_overrides.clear()

    def test_get_salary_by_location(self, client):
        """Test getting salary by location."""
        mock_data = [
            {
                "location": "San Francisco",
                "average_salary": 145000.0,
                "job_count": 200,
                "min_salary": 110000.0,
                "max_salary": 180000.0,
            }
        ]
        mock_service = Mock()
        mock_service.get_salary_by_location.return_value = mock_data

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/salary-by-location?limit=10")
            assert response.status_code == 200

            data = response.json()
            assert len(data) > 0
            assert "location" in data[0]
            assert "average_salary" in data[0]
        finally:
            app.dependency_overrides.clear()

    def test_get_posting_trend(self, client, sample_analytics_response):
        """Test getting posting trend."""
        mock_service = Mock()
        mock_service.get_posting_trend.return_value = sample_analytics_response["posting_trend"]

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/posting-trend?days=30")
            assert response.status_code == 200

            data = response.json()
            assert len(data) > 0
            assert "date" in data[0]
            assert "count" in data[0]
        finally:
            app.dependency_overrides.clear()

    def test_get_recent_jobs(self, client):
        """Test getting recent jobs count."""
        mock_service = Mock()
        mock_service.get_recent_jobs_count.return_value = 50

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/recent-jobs?days=7")
            assert response.status_code == 200
            assert response.json() == 50
        finally:
            app.dependency_overrides.clear()

    def test_get_salary_distribution(self, client):
        """Test getting salary distribution."""
        mock_data = [
            {"range": "0-30K", "count": 100, "percentage": 10.0},
            {"range": "30K-50K", "count": 200, "percentage": 20.0},
        ]
        mock_service = Mock()
        mock_service.get_salary_distribution.return_value = mock_data

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/salary-distribution")
            assert response.status_code == 200

            data = response.json()
            assert len(data) > 0
            assert "range" in data[0]
            assert "count" in data[0]
        finally:
            app.dependency_overrides.clear()

    def test_get_dataset_summary(self, client):
        """Test getting dataset summary."""
        mock_data = {
            "total_jobs": 1000,
            "unique_companies": 200,
            "unique_locations": 50,
            "unique_skills": 80,
            "date_range": {"earliest": "2026-01-01", "latest": "2026-01-31"},
            "last_updated": datetime.now().isoformat(),
        }
        mock_service = Mock()
        mock_service.get_dataset_summary.return_value = mock_data

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/dataset-summary")
            assert response.status_code == 200

            data = response.json()
            assert "total_jobs" in data
            assert "unique_companies" in data
            assert "date_range" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_overview(self, client):
        """Test getting overview."""
        mock_data = {
            "total_jobs": 1000,
            "recent_jobs": 50,
            "top_company": "TechCorp",
            "top_skill": "Python",
            "average_salary": 135000.0,
        }
        mock_service = Mock()
        mock_service.get_overview.return_value = mock_data

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/overview")
            assert response.status_code == 200

            data = response.json()
            assert "total_jobs" in data
            assert "top_company" in data
            assert "average_salary" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_dashboard_summary(self, client, sample_analytics_response):
        """Test getting dashboard summary."""
        mock_service = Mock()
        mock_service.get_dashboard_summary.return_value = sample_analytics_response

        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/dashboard-summary")
            assert response.status_code == 200

            data = response.json()
            assert "total_jobs" in data
            assert "top_skills" in data
            assert "salary_statistics" in data
            assert "posting_trend" in data
        finally:
            app.dependency_overrides.clear()

    def test_analytics_endpoint_invalid_limit(self, client):
        """Test analytics endpoint with invalid limit."""
        mock_service = Mock()
        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/top-skills?limit=1000")
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_analytics_endpoint_invalid_days(self, client):
        """Test analytics endpoint with invalid days."""
        mock_service = Mock()
        app.dependency_overrides[get_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/analytics/posting-trend?days=1000")
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()
