"""
Unit tests for dashboard API endpoints.
"""

from dashboard.api.endpoints import HEALTH, JOB_DETAIL, JOBS, endpoints


class TestDashboardEndpoints:
    """Test suite for dashboard API endpoints constants."""

    def test_health_endpoint(self):
        """Test health endpoint constant."""
        assert HEALTH == "/api/v1/health"
        assert endpoints.HEALTH == "/api/v1/health"

    def test_jobs_endpoints(self):
        """Test jobs endpoints constants."""
        assert JOBS == "/api/v1/jobs"
        assert JOB_DETAIL == "/api/v1/jobs/{job_id}"
        assert endpoints.JOBS == "/api/v1/jobs"
        assert endpoints.JOB_DETAIL == "/api/v1/jobs/{job_id}"

    def test_analytics_endpoints(self):
        """Test analytics endpoints constants."""
        assert endpoints.TOP_SKILLS == "/api/v1/analytics/top-skills"
        assert endpoints.TOP_COMPANIES == "/api/v1/analytics/top-companies"
        assert endpoints.JOBS_BY_LOCATION == "/api/v1/analytics/jobs-by-location"
        assert endpoints.SALARY_STATISTICS == "/api/v1/analytics/salary-statistics"
        assert endpoints.EMPLOYMENT_TYPES == "/api/v1/analytics/employment-types"
        assert endpoints.SALARY_BY_LOCATION == "/api/v1/analytics/salary-by-location"
        assert endpoints.SALARY_BY_COMPANY == "/api/v1/analytics/salary-by-company"
        assert endpoints.POSTING_TREND == "/api/v1/analytics/posting-trend"
        assert endpoints.RECENT_JOBS == "/api/v1/analytics/recent-jobs"
        assert endpoints.SALARY_DISTRIBUTION == "/api/v1/analytics/salary-distribution"
        assert endpoints.DATASET_SUMMARY == "/api/v1/analytics/dataset-summary"
        assert endpoints.OVERVIEW == "/api/v1/analytics/overview"
        assert endpoints.DASHBOARD_SUMMARY == "/api/v1/analytics/dashboard-summary"

    def test_all_endpoints_are_strings(self):
        """Test that all endpoint values are strings."""
        for attr_name in dir(endpoints):
            if not attr_name.startswith("_"):
                attr_value = getattr(endpoints, attr_name)
                assert isinstance(attr_value, str), f"{attr_name} is not a string"
