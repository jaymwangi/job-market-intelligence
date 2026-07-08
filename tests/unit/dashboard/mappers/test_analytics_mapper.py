"""
Unit tests for dashboard analytics mapper.
"""

import pytest

from dashboard.mappers.analytics_mapper import AnalyticsMapper
from dashboard.schemas.analytics import (
    DashboardSummary,
    EmploymentType,
    LocationAnalytics,
    SalaryDistribution,
    SalaryStatistics,
    TopCompany,
    TopSkill,
)
from dashboard.schemas.chart_data import (
    BarChartData,
    DonutChartData,
    HistogramData,
    HorizontalBarChartData,
    LineChartData,
    MetricCardData,
    PieChartData,
)


class TestAnalyticsMapper:
    """Test suite for AnalyticsMapper."""

    @pytest.fixture
    def mapper(self):
        return AnalyticsMapper()

    @pytest.fixture
    def sample_dashboard_summary(self):
        return DashboardSummary(
            total_jobs=1000,
            recent_jobs_count=50,
            top_companies=[
                TopCompany(company="TechCorp", job_count=120, percentage=12.0),
                TopCompany(company="DataInc", job_count=80, percentage=8.0),
            ],
            top_locations=[
                LocationAnalytics(location="San Francisco", job_count=200, percentage=20.0),
                LocationAnalytics(location="New York", job_count=150, percentage=15.0),
            ],
            top_skills=[
                TopSkill(skill="Python", count=450, percentage=25.0),
                TopSkill(skill="JavaScript", count=380, percentage=21.1),
            ],
            salary_statistics=SalaryStatistics(
                average=135000.0,
                minimum=100000.0,
                maximum=180000.0,
                median=130000.0,
                sample_size=500,
                currency="USD",
            ),
            employment_types=[
                EmploymentType(employment_type="Full-time", count=800, percentage=80.0),
                EmploymentType(employment_type="Contract", count=200, percentage=20.0),
            ],
            posting_trend=[],
        )

    def test_to_metric_cards_with_data(self, mapper, sample_dashboard_summary):
        """Test converting to metric cards with data."""
        cards = mapper.to_metric_cards(sample_dashboard_summary)

        assert len(cards) == 4
        assert isinstance(cards[0], MetricCardData)
        assert cards[0].title == "Total Jobs"
        assert cards[0].value == "1,000"
        assert cards[1].title == "Companies"
        assert cards[1].value == "N/A"  # unique_companies not in summary
        assert cards[2].title == "Skills"
        assert cards[2].value == "N/A"  # unique_skills not in summary
        assert cards[3].title == "Average Salary"
        assert cards[3].value == "$135,000"

    def test_to_metric_cards_empty(self, mapper):
        """Test converting to metric cards with empty data."""
        cards = mapper.to_metric_cards(None)
        assert cards == []

    def test_to_horizontal_bar_chart(self, mapper, sample_dashboard_summary):
        """Test converting to horizontal bar chart."""
        chart = mapper.to_horizontal_bar_chart(
            data=sample_dashboard_summary.top_companies,
            title="Top Companies",
            label_field="company",
            value_field="job_count",
            x_label="Jobs",
            y_label="Company",
        )

        assert isinstance(chart, HorizontalBarChartData)
        assert chart.title == "Top Companies"
        assert len(chart.x_values) == 2
        assert chart.x_values[0] == "TechCorp"
        assert chart.y_values[0] == 120.0
        assert chart.x_label == "Jobs"
        assert chart.y_label == "Company"

    def test_to_horizontal_bar_chart_empty(self, mapper):
        """Test converting to horizontal bar chart with empty data."""
        chart = mapper.to_horizontal_bar_chart(
            data=[], title="Empty Chart", label_field="name", value_field="count"
        )

        assert isinstance(chart, HorizontalBarChartData)
        assert chart.title == "Empty Chart"
        assert chart.x_values == []
        assert chart.y_values == []

    def test_to_bar_chart(self, mapper, sample_dashboard_summary):
        """Test converting to bar chart."""
        chart = mapper.to_bar_chart(
            data=sample_dashboard_summary.top_skills,
            title="Top Skills",
            label_field="skill",
            value_field="count",
            x_label="Skill",
            y_label="Count",
        )

        assert isinstance(chart, BarChartData)
        assert chart.title == "Top Skills"
        assert len(chart.x_values) == 2
        assert chart.x_values[0] == "Python"
        assert chart.y_values[0] == 450.0

    def test_to_bar_chart_empty(self, mapper):
        """Test converting to bar chart with empty data."""
        chart = mapper.to_bar_chart(
            data=[], title="Empty Chart", label_field="name", value_field="count"
        )

        assert isinstance(chart, BarChartData)
        assert chart.title == "Empty Chart"
        assert chart.x_values == []
        assert chart.y_values == []

    def test_to_pie_chart(self, mapper, sample_dashboard_summary):
        """Test converting to pie chart."""
        chart = mapper.to_pie_chart(
            data=sample_dashboard_summary.top_skills,
            title="Skill Distribution",
            label_field="skill",
            value_field="count",
            show_percentage=True,
        )

        assert isinstance(chart, PieChartData)
        assert chart.title == "Skill Distribution"
        assert len(chart.labels) == 2
        assert chart.labels[0] == "Python"
        assert chart.values[0] == 450.0
        assert chart.show_percentage is True

    def test_to_pie_chart_empty(self, mapper):
        """Test converting to pie chart with empty data."""
        chart = mapper.to_pie_chart(
            data=[], title="Empty Chart", label_field="name", value_field="count"
        )

        assert isinstance(chart, PieChartData)
        assert chart.title == "Empty Chart"
        assert chart.labels == []
        assert chart.values == []

    def test_to_donut_chart(self, mapper, sample_dashboard_summary):
        """Test converting to donut chart."""
        chart = mapper.to_donut_chart(
            data=sample_dashboard_summary.top_skills,
            title="Skill Distribution",
            label_field="skill",
            value_field="count",
            show_percentage=True,
            hole_size=0.5,
        )

        assert isinstance(chart, DonutChartData)
        assert chart.title == "Skill Distribution"
        assert len(chart.labels) == 2
        assert chart.labels[0] == "Python"
        assert chart.values[0] == 450.0
        assert chart.hole_size == 0.5

    def test_to_donut_chart_default_hole_size(self, mapper, sample_dashboard_summary):
        """Test converting to donut chart with default hole size."""
        chart = mapper.to_donut_chart(
            data=sample_dashboard_summary.top_skills,
            title="Skill Distribution",
            label_field="skill",
            value_field="count",
        )

        assert chart.hole_size == 0.4

    def test_to_line_chart(self, mapper):
        """Test converting to line chart."""

        # Create sample trend data
        class TrendItem:
            def __init__(self, date, count):
                self.date = date
                self.count = count

        data = [
            TrendItem("2026-01-01", 100),
            TrendItem("2026-01-02", 120),
            TrendItem("2026-01-03", 150),
        ]

        chart = mapper.to_line_chart(
            data=data,
            title="Job Postings Trend",
            x_field="date",
            y_field="count",
            x_label="Date",
            y_label="Jobs",
            fill_area=True,
            show_markers=True,
        )

        assert isinstance(chart, LineChartData)
        assert chart.title == "Job Postings Trend"
        assert len(chart.x_values) == 3
        assert chart.x_values[0] == "2026-01-01"
        assert chart.y_values[0] == 100.0
        assert chart.x_label == "Date"
        assert chart.y_label == "Jobs"
        assert chart.fill_area is True
        assert chart.show_markers is True

    def test_to_line_chart_empty(self, mapper):
        """Test converting to line chart with empty data."""
        chart = mapper.to_line_chart(data=[], title="Empty Chart", x_field="date", y_field="count")

        assert isinstance(chart, LineChartData)
        assert chart.title == "Empty Chart"
        assert chart.x_values == []
        assert chart.y_values == []

    def test_to_histogram(self, mapper):
        """Test converting to histogram."""

        # Create sample distribution data
        class DistributionItem:
            def __init__(self, range_val, count):
                self.range = range_val
                self.count = count

        data = [
            DistributionItem("$0-50k", 100),
            DistributionItem("$50-100k", 200),
            DistributionItem("$100-150k", 150),
        ]

        chart = mapper.to_histogram(
            data=data,
            title="Salary Distribution",
            range_field="range",
            count_field="count",
            x_label="Range",
            y_label="Count",
        )

        assert isinstance(chart, HistogramData)
        assert chart.title == "Salary Distribution"
        assert len(chart.bins) == 3
        assert chart.bins[0] == "$0-50k"
        assert chart.counts[0] == 100
        assert chart.x_label == "Range"
        assert chart.y_label == "Count"

    def test_to_histogram_empty(self, mapper):
        """Test converting to histogram with empty data."""
        chart = mapper.to_histogram(
            data=[], title="Empty Chart", range_field="range", count_field="count"
        )

        assert isinstance(chart, HistogramData)
        assert chart.title == "Empty Chart"
        assert chart.bins == []
        assert chart.counts == []

    def test_to_salary_histogram(self, mapper):
        """Test converting to salary histogram."""
        salary_distributions = [
            SalaryDistribution(range="$0-50k", count=100, percentage=10.0),
            SalaryDistribution(range="$50-100k", count=200, percentage=20.0),
            SalaryDistribution(range="$100-150k", count=150, percentage=15.0),
        ]

        chart = mapper.to_salary_histogram(salary_distributions)

        assert isinstance(chart, HistogramData)
        assert chart.title == "Salary Distribution"
        assert len(chart.bins) == 3
        assert chart.bins[0] == "$0-50k"
        assert chart.counts[0] == 100
        assert chart.x_label == "Salary Range"
        assert chart.y_label == "Number of Jobs"
        assert chart.color == "#d62728"

    def test_to_salary_histogram_empty(self, mapper):
        """Test converting to salary histogram with empty data."""
        chart = mapper.to_salary_histogram([])

        assert isinstance(chart, HistogramData)
        assert chart.title == "Salary Distribution"
        assert chart.bins == []
        assert chart.counts == []
