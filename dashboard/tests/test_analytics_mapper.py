# dashboard/tests/test_analytics_mapper.py
"""Tests for AnalyticsMapper."""

from dashboard.mappers.analytics_mapper import AnalyticsMapper
from dashboard.schemas.analytics import (DashboardSummary, EmploymentType,
                                         LocationAnalytics, PostingTrend,
                                         SalaryDistribution, SalaryStatistics,
                                         TopCompany, TopSkill)


class TestAnalyticsMapper:
    """Test suite for AnalyticsMapper."""

    def setup_method(self):
        """Set up test data."""
        self.mapper = AnalyticsMapper()

        self.sample_skills = [
            TopSkill(skill="Python", count=100, percentage=25.0),
            TopSkill(skill="SQL", count=80, percentage=20.0),
            TopSkill(skill="Java", count=60, percentage=15.0),
        ]

        self.sample_companies = [
            TopCompany(company="Google", job_count=150, percentage=30.0),
            TopCompany(company="Microsoft", job_count=120, percentage=24.0),
            TopCompany(company="Amazon", job_count=90, percentage=18.0),
        ]

        self.sample_locations = [
            LocationAnalytics(location="San Francisco", job_count=200, percentage=25.0),
            LocationAnalytics(location="New York", job_count=160, percentage=20.0),
            LocationAnalytics(location="Remote", job_count=120, percentage=15.0),
        ]

        self.sample_salary_stats = SalaryStatistics(
            average=120000,
            minimum=80000,
            maximum=200000,
            median=115000,
            sample_size=500,
            currency="USD",
        )

        self.sample_employment = [
            EmploymentType(employment_type="Full-time", count=300, percentage=60.0),
            EmploymentType(employment_type="Contract", count=150, percentage=30.0),
            EmploymentType(employment_type="Part-time", count=50, percentage=10.0),
        ]

        self.sample_trends = [
            PostingTrend(date="2024-01-01", count=10, cumulative=10),
            PostingTrend(date="2024-01-02", count=15, cumulative=25),
            PostingTrend(date="2024-01-03", count=12, cumulative=37),
        ]

    def test_to_metric_cards(self):
        """Test conversion to metric cards."""
        # Create summary with fields that actually exist in your schema
        summary = DashboardSummary(
            total_jobs=1000,
            recent_jobs_count=100,
            top_companies=self.sample_companies,
            top_locations=self.sample_locations,
            top_skills=self.sample_skills,
            salary_statistics=self.sample_salary_stats,
            employment_types=self.sample_employment,
            posting_trend=self.sample_trends,
        )

        metrics = self.mapper.to_metric_cards(summary)

        assert len(metrics) == 4
        assert metrics[0].title == "Total Jobs"
        assert metrics[0].value == "1,000"
        # The mapper uses getattr with defaults for companies and skills
        assert metrics[1].title == "Companies"
        assert metrics[2].title == "Skills"
        assert metrics[3].title == "Average Salary"
        assert metrics[3].value == "$120,000"

    def test_to_metric_cards_empty(self):
        """Test conversion with empty summary."""
        metrics = self.mapper.to_metric_cards(None)
        assert metrics == []

    def test_to_metric_cards_without_optional_fields(self):
        """Test conversion with summary missing optional fields."""
        # If your schema doesn't have unique_companies or unique_skills,
        # the mapper should handle it gracefully
        summary = DashboardSummary(
            total_jobs=1000,
            recent_jobs_count=100,
            top_companies=[],
            top_locations=[],
            top_skills=[],
            salary_statistics=self.sample_salary_stats,
            employment_types=[],
            posting_trend=[],
        )

        metrics = self.mapper.to_metric_cards(summary)

        # Should still work with defaults (N/A for missing fields)
        assert len(metrics) == 4
        assert metrics[0].title == "Total Jobs"
        assert metrics[0].value == "1,000"

    def test_to_horizontal_bar_chart(self):
        """Test conversion to horizontal bar chart."""
        chart = self.mapper.to_horizontal_bar_chart(
            data=self.sample_skills,
            title="Top Skills",
            label_field="skill",
            value_field="count",
            x_label="Count",
            y_label="Skill",
        )

        assert chart.title == "Top Skills"
        assert chart.x_values == ["Python", "SQL", "Java"]
        assert chart.y_values == [100.0, 80.0, 60.0]
        assert chart.x_label == "Count"
        assert chart.y_label == "Skill"

    def test_to_horizontal_bar_chart_empty(self):
        """Test conversion with empty data."""
        chart = self.mapper.to_horizontal_bar_chart(
            data=[], title="Empty Chart", label_field="skill", value_field="count"
        )

        assert chart.title == "Empty Chart"
        assert chart.x_values == []
        assert chart.y_values == []

    def test_to_pie_chart(self):
        """Test conversion to pie chart."""
        chart = self.mapper.to_pie_chart(
            data=self.sample_skills,
            title="Skill Distribution",
            label_field="skill",
            value_field="count",
            show_percentage=True,
        )

        assert chart.title == "Skill Distribution"
        assert chart.labels == ["Python", "SQL", "Java"]
        assert chart.values == [100.0, 80.0, 60.0]
        assert chart.show_percentage is True

    def test_to_donut_chart(self):
        """Test conversion to donut chart."""
        chart = self.mapper.to_donut_chart(
            data=self.sample_companies,
            title="Company Distribution",
            label_field="company",
            value_field="job_count",
            show_percentage=True,
            hole_size=0.5,
        )

        assert chart.title == "Company Distribution"
        assert chart.labels == ["Google", "Microsoft", "Amazon"]
        assert chart.values == [150.0, 120.0, 90.0]
        assert chart.hole_size == 0.5

    def test_to_line_chart(self):
        """Test conversion to line chart."""
        chart = self.mapper.to_line_chart(
            data=self.sample_trends,
            title="Posting Trends",
            x_field="date",
            y_field="cumulative",
            x_label="Date",
            y_label="Cumulative Jobs",
            fill_area=True,
            show_markers=True,
        )

        assert chart.title == "Posting Trends"
        assert chart.x_values == ["2024-01-01", "2024-01-02", "2024-01-03"]
        assert chart.y_values == [10.0, 25.0, 37.0]
        assert chart.fill_area is True
        assert chart.show_markers is True

    def test_to_histogram(self):
        """Test conversion to histogram."""
        distribution = [
            SalaryDistribution(range="$0-$50k", count=100, percentage=20.0),
            SalaryDistribution(range="$50k-$100k", count=200, percentage=40.0),
            SalaryDistribution(range="$100k-$150k", count=150, percentage=30.0),
            SalaryDistribution(range="$150k+", count=50, percentage=10.0),
        ]

        chart = self.mapper.to_salary_histogram(distribution)

        assert chart.title == "Salary Distribution"
        assert chart.bins == ["$0-$50k", "$50k-$100k", "$100k-$150k", "$150k+"]
        assert chart.counts == [100, 200, 150, 50]
        assert chart.x_label == "Salary Range"
        assert chart.y_label == "Number of Jobs"
