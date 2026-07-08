# dashboard/mappers/analytics_mapper.py
"""Presentation layer mapper with feature-specific public methods."""

from ..schemas.analytics import DashboardSummary, SalaryDistribution
from ..schemas.chart_data import (
    BarChartData,
    DonutChartData,
    HistogramData,
    HorizontalBarChartData,
    LineChartData,
    MetricCardData,
    PieChartData,
)


class AnalyticsMapper:
    """Transforms domain models to presentation chart models."""

    def to_metric_cards(self, summary: DashboardSummary | None) -> list[MetricCardData]:
        """Transform dashboard summary to metric cards."""
        if not summary:
            return []

        # Safe attribute access with defaults
        total_jobs = getattr(summary, "total_jobs", 0)
        unique_companies = getattr(summary, "unique_companies", 0)
        unique_skills = getattr(summary, "unique_skills", 0)
        salary_stats = getattr(summary, "salary_statistics", None)

        avg_salary = salary_stats.average if salary_stats else 0
        currency = salary_stats.currency if salary_stats else "USD"

        return [
            MetricCardData(title="Total Jobs", value=f"{total_jobs:,}", icon="📊", color="#1f77b4"),
            MetricCardData(
                title="Companies",
                value=f"{unique_companies:,}" if unique_companies > 0 else "N/A",
                icon="🏢",
                color="#2ca02c",
            ),
            MetricCardData(
                title="Skills",
                value=f"{unique_skills:,}" if unique_skills > 0 else "N/A",
                icon="🎯",
                color="#ff7f0e",
            ),
            MetricCardData(
                title="Average Salary",
                value=f"${avg_salary:,.0f}" if avg_salary > 0 else "N/A",
                subtitle=currency,
                icon="💰",
                color="#d62728",
            ),
        ]

    def to_horizontal_bar_chart(
        self,
        data: list,
        title: str,
        label_field: str,
        value_field: str,
        x_label: str = "Count",
        y_label: str = "",
        color: str = "#1f77b4",
        show_values: bool = True,
    ) -> HorizontalBarChartData:
        """Transform data to horizontal bar chart."""
        if not data:
            return HorizontalBarChartData(
                title=title, x_values=[], y_values=[], x_label=x_label, y_label=y_label
            )

        # Sort by value descending
        sorted_data = sorted(data, key=lambda x: getattr(x, value_field), reverse=True)

        return HorizontalBarChartData(
            title=title,
            x_values=[getattr(item, label_field) for item in sorted_data],
            y_values=[float(getattr(item, value_field)) for item in sorted_data],
            x_label=x_label,
            y_label=y_label,
            color=color,
            show_values=show_values,
        )

    def to_bar_chart(
        self,
        data: list,
        title: str,
        label_field: str,
        value_field: str,
        x_label: str = "",
        y_label: str = "",
        color: str = "#1f77b4",
        show_values: bool = False,
    ) -> BarChartData:
        """Transform data to bar chart."""
        if not data:
            return BarChartData(
                title=title, x_values=[], y_values=[], x_label=x_label, y_label=y_label
            )

        sorted_data = sorted(data, key=lambda x: getattr(x, value_field), reverse=True)

        return BarChartData(
            title=title,
            x_values=[getattr(item, label_field) for item in sorted_data],
            y_values=[float(getattr(item, value_field)) for item in sorted_data],
            x_label=x_label,
            y_label=y_label,
            color=color,
            show_values=show_values,
        )

    def to_pie_chart(
        self,
        data: list,
        title: str,
        label_field: str,
        value_field: str,
        show_percentage: bool = True,
    ) -> PieChartData:
        """Transform data to pie chart."""
        if not data:
            return PieChartData(title=title, labels=[], values=[])

        return PieChartData(
            title=title,
            labels=[getattr(item, label_field) for item in data],
            values=[float(getattr(item, value_field)) for item in data],
            show_percentage=show_percentage,
        )

    def to_donut_chart(
        self,
        data: list,
        title: str,
        label_field: str,
        value_field: str,
        show_percentage: bool = True,
        hole_size: float = 0.4,
    ) -> DonutChartData:
        """Transform data to donut chart."""
        if not data:
            return DonutChartData(title=title, labels=[], values=[])

        return DonutChartData(
            title=title,
            labels=[getattr(item, label_field) for item in data],
            values=[float(getattr(item, value_field)) for item in data],
            show_percentage=show_percentage,
            hole_size=hole_size,
        )

    def to_line_chart(
        self,
        data: list,
        title: str,
        x_field: str,
        y_field: str,
        x_label: str = "Date",
        y_label: str = "Count",
        fill_area: bool = False,
        show_markers: bool = True,
    ) -> LineChartData:
        """Transform data to line chart."""
        if not data:
            return LineChartData(
                title=title, x_values=[], y_values=[], x_label=x_label, y_label=y_label
            )

        sorted_data = sorted(data, key=lambda x: getattr(x, x_field))

        return LineChartData(
            title=title,
            x_values=[str(getattr(item, x_field)) for item in sorted_data],
            y_values=[float(getattr(item, y_field)) for item in sorted_data],
            x_label=x_label,
            y_label=y_label,
            fill_area=fill_area,
            show_markers=show_markers,
        )

    def to_histogram(
        self,
        data: list,
        title: str,
        range_field: str,
        count_field: str,
        x_label: str = "Range",
        y_label: str = "Count",
        color: str = "#1f77b4",
    ) -> HistogramData:
        """Transform distribution data to histogram."""
        if not data:
            return HistogramData(title=title, bins=[], counts=[], x_label=x_label, y_label=y_label)

        return HistogramData(
            title=title,
            bins=[getattr(item, range_field) for item in data],
            counts=[getattr(item, count_field) for item in data],
            x_label=x_label,
            y_label=y_label,
            color=color,
        )

    def to_salary_histogram(self, distribution: list[SalaryDistribution]) -> HistogramData:
        """Transform salary distribution to histogram."""
        return self.to_histogram(
            data=distribution,
            title="Salary Distribution",
            range_field="range",
            count_field="count",
            x_label="Salary Range",
            y_label="Number of Jobs",
            color="#d62728",
        )
