"""Tests for reusable Plotly chart components."""

import plotly.graph_objects as go

from dashboard.components.charts import (
    create_bar_chart,
    create_donut_chart,
    create_histogram,
    create_horizontal_bar_chart,
    create_line_chart,
    create_pie_chart,
)
from dashboard.schemas.chart_data import (
    BarChartData,
    DonutChartData,
    HistogramData,
    HorizontalBarChartData,
    LineChartData,
    PieChartData,
)


class TestCreateBarChart:
    """Tests for create_bar_chart."""

    def test_creates_bar_chart_with_data(self) -> None:
        data = BarChartData(
            title="Jobs by Location",
            x_values=["Nairobi", "Mombasa"],
            y_values=[100, 50],
            x_label="Location",
            y_label="Jobs",
            color="#123456",
            show_values=True,
        )

        fig = create_bar_chart(data)

        traces = list(fig.data)
        assert len(traces) == 1
        trace = traces[0]
        assert isinstance(trace, go.Bar)
        trace_json = trace.to_plotly_json()
        assert trace.type == "bar"
        assert trace_json["x"] == ["Nairobi", "Mombasa"]
        assert trace_json["y"] == [100, 50]
        assert trace_json["marker"]["color"] == "#123456"
        assert trace_json["text"] == ["100.0", "50.0"]
        assert fig.layout.title.text == "Jobs by Location"
        assert fig.layout.xaxis.title.text == "Location"
        assert fig.layout.yaxis.title.text == "Jobs"

    def test_creates_empty_bar_chart(self) -> None:
        data = BarChartData(
            title="No Jobs",
            x_values=[],
            y_values=[],
        )

        fig = create_bar_chart(data)

        traces = list(fig.data)
        assert len(traces) == 0
        assert fig.layout.title.text == "No Jobs"
        assert fig.layout.annotations[0].text == "No data available"

    def test_bar_chart_hides_values_when_disabled(self) -> None:
        data = BarChartData(
            title="Jobs",
            x_values=["Nairobi"],
            y_values=[100],
            show_values=False,
        )

        fig = create_bar_chart(data)

        trace = fig.data[0]
        assert isinstance(trace, go.Bar)
        trace_json = trace.to_plotly_json()
        assert "text" not in trace_json
        assert "textposition" not in trace_json


class TestCreateHorizontalBarChart:
    """Tests for create_horizontal_bar_chart."""

    def test_creates_horizontal_bar_chart_with_data(self) -> None:
        data = HorizontalBarChartData(
            title="Jobs by Skill",
            x_values=["Python", "SQL"],
            y_values=[100, 80],
            x_label="Skill",
            y_label="Jobs",
            color="#654321",
            show_values=True,
            sort_by="value",
        )

        fig = create_horizontal_bar_chart(data)

        traces = list(fig.data)
        assert len(traces) == 1
        trace = traces[0]
        assert isinstance(trace, go.Bar)
        trace_json = trace.to_plotly_json()
        assert trace.type == "bar"
        assert trace_json["orientation"] == "h"
        assert trace_json["y"] == ["Python", "SQL"]
        assert trace_json["x"] == [100, 80]
        assert trace_json["marker"]["color"] == "#654321"
        assert trace_json["text"] == ["100.0", "80.0"]
        assert fig.layout.yaxis.categoryorder == "total ascending"
        assert fig.layout.height == 400

    def test_horizontal_bar_height_grows_with_many_values(self) -> None:
        data = HorizontalBarChartData(
            title="Many Skills",
            x_values=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O"],
            y_values=[1] * 15,
        )

        fig = create_horizontal_bar_chart(data)

        assert fig.layout.height == 550

    def test_creates_empty_horizontal_bar_chart(self) -> None:
        data = HorizontalBarChartData(
            title="No Skills",
            x_values=[],
            y_values=[],
        )

        fig = create_horizontal_bar_chart(data)

        traces = list(fig.data)
        assert len(traces) == 0
        assert fig.layout.title.text == "No Skills"
        assert fig.layout.annotations[0].text == "No data available"


class TestCreatePieChart:
    """Tests for create_pie_chart."""

    def test_creates_pie_chart_with_data(self) -> None:
        data = PieChartData(
            title="Jobs by Type",
            labels=["Full-time", "Contract"],
            values=[80, 20],
            show_percentage=True,
            color_sequence=["red", "blue"],
        )

        fig = create_pie_chart(data)

        traces = list(fig.data)
        assert len(traces) == 1
        trace = traces[0]
        assert isinstance(trace, go.Pie)
        trace_json = trace.to_plotly_json()
        assert trace.type == "pie"
        assert trace_json["labels"] == ["Full-time", "Contract"]
        assert trace_json["values"] == [80, 20]
        assert trace_json["textinfo"] == "label+percent"
        assert trace_json["marker"]["colors"] == ["red", "blue"]
        assert fig.layout.title.text == "Jobs by Type"

    def test_pie_chart_can_hide_percentages(self) -> None:
        data = PieChartData(
            title="Jobs",
            labels=["A", "B"],
            values=[60, 40],
            show_percentage=False,
        )

        fig = create_pie_chart(data)

        trace = fig.data[0]
        assert isinstance(trace, go.Pie)
        trace_json = trace.to_plotly_json()
        assert trace.textinfo == "label"

    def test_creates_empty_pie_chart(self) -> None:
        data = PieChartData(
            title="No Jobs",
            labels=[],
            values=[],
        )

        fig = create_pie_chart(data)

        traces = list(fig.data)
        assert len(traces) == 0
        assert fig.layout.title.text == "No Jobs"
        assert fig.layout.annotations[0].text == "No data available"


class TestCreateDonutChart:
    """Tests for create_donut_chart."""

    def test_creates_donut_chart_with_data(self) -> None:
        data = DonutChartData(
            title="Employment Types",
            labels=["Full-time", "Contract"],
            values=[75, 25],
            hole_size=0.6,
            color_sequence=["green", "orange"],
        )

        fig = create_donut_chart(data)

        traces = list(fig.data)
        assert len(traces) == 1
        trace = traces[0]
        assert isinstance(trace, go.Pie)
        trace_json = trace.to_plotly_json()
        assert trace.type == "pie"
        assert trace_json["hole"] == 0.6
        assert trace_json["labels"] == ["Full-time", "Contract"]
        assert trace_json["values"] == [75, 25]
        assert trace_json["marker"]["colors"] == ["green", "orange"]

    def test_donut_chart_can_hide_percentages(self) -> None:
        data = DonutChartData(
            title="Jobs",
            labels=["A", "B"],
            values=[70, 30],
            show_percentage=False,
        )

        fig = create_donut_chart(data)

        trace = fig.data[0]
        assert isinstance(trace, go.Pie)
        trace_json = trace.to_plotly_json()
        assert trace.textinfo == "label"

    def test_creates_empty_donut_chart(self) -> None:
        data = DonutChartData(
            title="No Jobs",
            labels=[],
            values=[],
        )

        fig = create_donut_chart(data)

        traces = list(fig.data)
        assert len(traces) == 0
        assert fig.layout.title.text == "No Jobs"
        assert fig.layout.annotations[0].text == "No data available"


class TestCreateLineChart:
    """Tests for create_line_chart."""

    def test_creates_line_chart_with_markers_and_fill(self) -> None:
        data = LineChartData(
            title="Jobs Over Time",
            x_values=["Mon", "Tue", "Wed"],
            y_values=[10, 20, 15],
            x_label="Day",
            y_label="Jobs",
            fill_area=True,
            show_markers=True,
            color="#abcdef",
        )

        fig = create_line_chart(data)

        traces = list(fig.data)
        assert len(traces) == 1
        trace = traces[0]
        assert isinstance(trace, go.Scatter)
        trace_json = trace.to_plotly_json()
        assert trace.type == "scatter"
        assert trace_json["mode"] == "lines+markers"
        assert trace_json["fill"] == "tozeroy"
        assert trace_json["line"]["color"] == "#abcdef"
        assert trace_json["marker"]["color"] == "#abcdef"
        assert fig.layout.title.text == "Jobs Over Time"
        assert fig.layout.xaxis.title.text == "Day"
        assert fig.layout.yaxis.title.text == "Jobs"

    def test_line_chart_can_disable_markers_and_fill(self) -> None:
        data = LineChartData(
            title="Jobs",
            x_values=["Mon", "Tue"],
            y_values=[10, 20],
            fill_area=False,
            show_markers=False,
        )

        fig = create_line_chart(data)

        trace = fig.data[0]
        assert isinstance(trace, go.Scatter)
        trace_json = trace.to_plotly_json()
        assert trace_json["mode"] == "lines"
        assert "fill" not in trace_json

    def test_creates_empty_line_chart(self) -> None:
        data = LineChartData(
            title="No Jobs",
            x_values=[],
            y_values=[],
        )

        fig = create_line_chart(data)

        traces = list(fig.data)
        assert len(traces) == 0
        assert fig.layout.title.text == "No Jobs"
        assert fig.layout.annotations[0].text == "No data available"


class TestCreateHistogram:
    """Tests for create_histogram."""

    def test_creates_histogram_with_data(self) -> None:
        data = HistogramData(
            title="Salary Distribution",
            bins=["0-50k", "50-100k", "100-150k"],
            counts=[10, 30, 20],
            x_label="Salary",
            y_label="Jobs",
            color="#abcdef",
        )

        fig = create_histogram(data)

        traces = list(fig.data)
        assert len(traces) == 1
        trace = traces[0]
        assert isinstance(trace, go.Bar)
        trace_json = trace.to_plotly_json()
        assert trace.type == "bar"
        assert trace_json["x"] == ["0-50k", "50-100k", "100-150k"]
        assert trace_json["y"] == [10, 30, 20]
        assert trace_json["marker"]["color"] == "#abcdef"
        assert fig.layout.title.text == "Salary Distribution"
        assert fig.layout.xaxis.title.text == "Salary"
        assert fig.layout.yaxis.title.text == "Jobs"
        assert fig.layout.bargap == 0.05

    def test_creates_empty_histogram(self) -> None:
        data = HistogramData(
            title="No Salaries",
            bins=[],
            counts=[],
        )

        fig = create_histogram(data)

        traces = list(fig.data)
        assert len(traces) == 0
        assert fig.layout.title.text == "No Salaries"
        assert fig.layout.annotations[0].text == "No data available"