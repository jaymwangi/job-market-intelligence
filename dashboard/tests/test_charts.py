# dashboard/tests/test_analytics_service.py
"""Tests for AnalyticsService."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from dashboard.services.analytics_service import AnalyticsService
from dashboard.schemas.analytics import (
    DashboardSummary, TopSkill, TopCompany, LocationAnalytics,
    SalaryStatistics, SalaryDistribution, EmploymentType, PostingTrend
)
from dashboard.schemas.chart_data import (
    MetricCardData, HorizontalBarChartData, BarChartData,
    PieChartData, DonutChartData, LineChartData, HistogramData
)
from dashboard.mappers.analytics_mapper import AnalyticsMapper


class TestAnalyticsService:
    """Test suite for AnalyticsService."""
    
    def setup_method(self):
        """Set up test data."""
        self.mock_client = Mock()
        self.service = AnalyticsService(self.mock_client)
        
        # Sample API responses
        self.sample_dashboard_summary = {
            "total_jobs": 1000,
            "recent_jobs_count": 100,
            "top_companies": [
                {"company": "Google", "job_count": 150, "percentage": 30.0},
                {"company": "Microsoft", "job_count": 120, "percentage": 24.0},
            ],
            "top_locations": [
                {"location": "San Francisco", "job_count": 200, "percentage": 25.0},
            ],
            "top_skills": [
                {"skill": "Python", "count": 100, "percentage": 25.0},
                {"skill": "SQL", "count": 80, "percentage": 20.0},
            ],
            "salary_statistics": {
                "average": 120000,
                "minimum": 80000,
                "maximum": 200000,
                "median": 115000,
                "sample_size": 500,
                "currency": "USD"
            },
            "employment_types": [
                {"employment_type": "Full-time", "count": 300, "percentage": 60.0},
            ],
            "posting_trend": [
                {"date": "2024-01-01", "count": 10, "cumulative": 10},
                {"date": "2024-01-02", "count": 15, "cumulative": 25},
            ]
        }
        
        self.sample_top_skills = [
            {"skill": "Python", "count": 100, "percentage": 25.0},
            {"skill": "SQL", "count": 80, "percentage": 20.0},
            {"skill": "Java", "count": 60, "percentage": 15.0},
        ]
        
        self.sample_top_companies = [
            {"company": "Google", "job_count": 150, "percentage": 30.0},
            {"company": "Microsoft", "job_count": 120, "percentage": 24.0},
        ]
        
        self.sample_locations = [
            {"location": "San Francisco", "job_count": 200, "percentage": 25.0},
            {"location": "New York", "job_count": 160, "percentage": 20.0},
        ]
        
        self.sample_salary_stats = {
            "average": 120000,
            "minimum": 80000,
            "maximum": 200000,
            "median": 115000,
            "sample_size": 500,
            "currency": "USD"
        }
        
        self.sample_salary_distribution = [
            {"range": "$0-$50k", "count": 100, "percentage": 20.0},
            {"range": "$50k-$100k", "count": 200, "percentage": 40.0},
        ]
        
        self.sample_employment_types = [
            {"employment_type": "Full-time", "count": 300, "percentage": 60.0},
            {"employment_type": "Contract", "count": 150, "percentage": 30.0},
        ]
        
        self.sample_posting_trend = [
            {"date": "2024-01-01", "count": 10, "cumulative": 10},
            {"date": "2024-01-02", "count": 15, "cumulative": 25},
            {"date": "2024-01-03", "count": 12, "cumulative": 37},
        ]
    
    # ========== Dashboard Metrics Tests ==========
    
    def test_get_dashboard_metrics_success(self):
        """Test successful retrieval of dashboard metrics."""
        self.mock_client.get.return_value = self.sample_dashboard_summary
        
        metrics = self.service.get_dashboard_metrics()
        
        assert len(metrics) == 4
        assert metrics[0].title == "Total Jobs"
        assert metrics[0].value == "1,000"
        assert metrics[3].title == "Average Salary"
        assert metrics[3].value == "$120,000"
    
    def test_get_dashboard_metrics_failure(self):
        """Test failure handling in dashboard metrics."""
        self.mock_client.get.side_effect = Exception("API error")
        
        metrics = self.service.get_dashboard_metrics()
        
        assert metrics == []  # Should return empty list on failure
    
    # ========== Skills Chart Tests ==========
    
    def test_get_skills_chart_success(self):
        """Test successful retrieval of skills chart."""
        self.mock_client.get.return_value = self.sample_top_skills
        
        chart = self.service.get_skills_chart(limit=10)
        
        assert chart.title == "Most In-Demand Skills"
        assert chart.x_values == ["Python", "SQL", "Java"]
        assert chart.y_values == [100.0, 80.0, 60.0]
        assert chart.x_label == "Job Count"
        assert chart.y_label == "Skill"
    
    def test_get_skills_chart_failure(self):
        """Test failure handling in skills chart."""
        self.mock_client.get.side_effect = Exception("API error")
        
        chart = self.service.get_skills_chart(limit=10)
        
        assert chart.title == "Most In-Demand Skills"
        assert chart.x_values == []  # Should return empty chart on failure
    
    def test_get_skills_distribution_chart_success(self):
        """Test successful retrieval of skills distribution chart."""
        self.mock_client.get.return_value = self.sample_top_skills
        
        chart = self.service.get_skills_distribution_chart(limit=8)
        
        assert chart.title == "Skill Distribution"
        assert chart.labels == ["Python", "SQL", "Java"]
        assert chart.values == [100.0, 80.0, 60.0]
        assert chart.show_percentage is True
    
    def test_get_skills_distribution_chart_failure(self):
        """Test failure handling in skills distribution chart."""
        self.mock_client.get.side_effect = Exception("API error")
        
        chart = self.service.get_skills_distribution_chart(limit=8)
        
        assert chart.title == "Skill Distribution"
        assert chart.labels == []
        assert chart.values == []
    
    # ========== Companies Chart Tests ==========
    
    def test_get_companies_chart_success(self):
        """Test successful retrieval of companies chart."""
        self.mock_client.get.return_value = self.sample_top_companies
        
        chart = self.service.get_companies_chart(limit=10)
        
        assert chart.title == "Top Companies by Job Postings"
        assert chart.x_values == ["Google", "Microsoft"]
        assert chart.y_values == [150.0, 120.0]
    
    def test_get_companies_chart_failure(self):
        """Test failure handling in companies chart."""
        self.mock_client.get.side_effect = Exception("API error")
        
        chart = self.service.get_companies_chart(limit=10)
        
        assert chart.title == "Top Companies by Job Postings"
        assert chart.x_values == []
    
    def test_get_companies_distribution_chart_success(self):
        """Test successful retrieval of companies distribution chart."""
        self.mock_client.get.return_value = self.sample_top_companies
        
        chart = self.service.get_companies_distribution_chart(limit=8)
        
        assert chart.title == "Company Distribution"
        assert chart.labels == ["Google", "Microsoft"]
        assert chart.values == [150.0, 120.0]
        assert chart.hole_size == 0.4
    
    # ========== Locations Chart Tests ==========
    
    def test_get_locations_chart_success(self):
        """Test successful retrieval of locations chart."""
        self.mock_client.get.return_value = self.sample_locations
        
        chart = self.service.get_locations_chart(limit=10)
        
        assert chart.title == "Top Locations by Job Count"
        assert chart.x_values == ["San Francisco", "New York"]
        assert chart.y_values == [200.0, 160.0]
    
    def test_get_locations_chart_failure(self):
        """Test failure handling in locations chart."""
        self.mock_client.get.side_effect = Exception("API error")
        
        chart = self.service.get_locations_chart(limit=10)
        
        assert chart.title == "Top Locations by Job Count"
        assert chart.x_values == []
    
    # ========== Salary Tests ==========
    
    def test_get_salary_statistics_success(self):
        """Test successful retrieval of salary statistics."""
        self.mock_client.get.return_value = self.sample_salary_stats
        
        stats = self.service.get_salary_statistics()
        
        assert stats is not None
        assert stats.average == 120000
        assert stats.minimum == 80000
        assert stats.maximum == 200000
        assert stats.median == 115000
        assert stats.sample_size == 500
        assert stats.currency == "USD"
    
    def test_get_salary_statistics_failure(self):
        """Test failure handling in salary statistics."""
        self.mock_client.get.side_effect = Exception("API error")
        
        stats = self.service.get_salary_statistics()
        
        assert stats is None
    
    def test_get_salary_distribution_chart_success(self):
        """Test successful retrieval of salary distribution chart."""
        self.mock_client.get.return_value = self.sample_salary_distribution
        
        chart = self.service.get_salary_distribution_chart()
        
        assert chart.title == "Salary Distribution"
        assert chart.bins == ["$0-$50k", "$50k-$100k"]
        assert chart.counts == [100, 200]
        assert chart.x_label == "Salary Range"
        assert chart.y_label == "Number of Jobs"
    
    def test_get_salary_distribution_chart_failure(self):
        """Test failure handling in salary distribution chart."""
        self.mock_client.get.side_effect = Exception("API error")
        
        chart = self.service.get_salary_distribution_chart()
        
        assert chart.title == "Salary Distribution"
        assert chart.bins == []
        assert chart.counts == []
    
    # ========== Employment Types Tests ==========
    
    def test_get_employment_types_chart_success(self):
        """Test successful retrieval of employment types chart."""
        self.mock_client.get.return_value = self.sample_employment_types
        
        chart = self.service.get_employment_types_chart()
        
        assert chart.title == "Employment Type Distribution"
        assert chart.labels == ["Full-time", "Contract"]
        assert chart.values == [300.0, 150.0]
        assert chart.hole_size == 0.4
    
    def test_get_employment_types_chart_failure(self):
        """Test failure handling in employment types chart."""
        self.mock_client.get.side_effect = Exception("API error")
        
        chart = self.service.get_employment_types_chart()
        
        assert chart.title == "Employment Type Distribution"
        assert chart.labels == []
        assert chart.values == []
    
    def test_get_employment_types_bar_chart_success(self):
        """Test successful retrieval of employment types bar chart."""
        self.mock_client.get.return_value = self.sample_employment_types
        
        chart = self.service.get_employment_types_bar_chart()
        
        assert chart.title == "Employment Type Counts"
        assert chart.x_values == ["Full-time", "Contract"]
        assert chart.y_values == [300.0, 150.0]
    
    # ========== Posting Trend Tests ==========
    
    def test_get_posting_trend_chart_success(self):
        """Test successful retrieval of posting trend chart."""
        self.mock_client.get.return_value = self.sample_posting_trend
        
        chart = self.service.get_posting_trend_chart(days=30)
        
        assert chart.title == "Job Postings Over Time (Last 30 Days)"
        assert chart.x_values == ["2024-01-01", "2024-01-02", "2024-01-03"]
        assert chart.y_values == [10.0, 25.0, 37.0]
        assert chart.fill_area is True
        assert chart.show_markers is True
    
    def test_get_posting_trend_chart_failure(self):
        """Test failure handling in posting trend chart."""
        self.mock_client.get.side_effect = Exception("API error")
        
        chart = self.service.get_posting_trend_chart(days=30)
        
        assert chart.title == "Job Postings Over Time"
        assert chart.x_values == []
        assert chart.y_values == []
    
    def test_get_daily_posting_trend_chart_success(self):
        """Test successful retrieval of daily posting trend chart."""
        self.mock_client.get.return_value = self.sample_posting_trend
        
        chart = self.service.get_daily_posting_trend_chart(days=30)
        
        assert chart.title == "Daily Job Postings"
        assert chart.x_values == ["2024-01-01", "2024-01-02", "2024-01-03"]
        assert chart.y_values == [10.0, 15.0, 12.0]
        assert chart.fill_area is False
        assert chart.show_markers is True
    
    # ========== Cache Tests ==========
    
    def test_refresh_all_clears_cache(self):
        """Test that refresh_all clears the cache."""
        mock_cache = Mock()
        self.service.cache_manager = mock_cache
        
        self.service.refresh_all()
        
        # Verify clear was called exactly once
        mock_cache.clear.assert_called_once()
    
    def test_refresh_all_called_when_cache_present(self):
        """Test refresh_all when cache is present."""
        mock_cache = Mock()
        self.service.cache_manager = mock_cache
        
        self.service.refresh_all()
        
        # Alternative verification
        assert mock_cache.clear.called
        assert mock_cache.clear.call_count == 1