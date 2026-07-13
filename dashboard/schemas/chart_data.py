# dashboard/schemas/chart_data.py
"""Chart models for presentation layer."""

from enum import StrEnum

from pydantic import BaseModel


class ChartType(StrEnum):
    """Types of charts."""

    BAR = "bar"
    HORIZONTAL_BAR = "horizontal_bar"
    PIE = "pie"
    DONUT = "donut"
    LINE = "line"
    HISTOGRAM = "histogram"


class MetricCardData(BaseModel):
    """Data for a metric card."""

    title: str
    value: str
    change: float | None = None
    change_direction: str | None = None  # "up" or "down"
    icon: str | None = None
    color: str | None = None
    subtitle: str | None = None


class BarChartData(BaseModel):
    """Data for bar chart."""

    title: str
    x_values: list[str]
    y_values: list[float]
    x_label: str = ""
    y_label: str = ""
    color: str | None = None
    show_values: bool = False
    sort_by: str | None = None  # "value" or "label"
    sort_descending: bool = True


class HorizontalBarChartData(BarChartData):
    """Data for horizontal bar chart."""

    pass


class PieChartData(BaseModel):
    """Data for pie/donut chart."""

    title: str
    labels: list[str]
    values: list[float]
    show_percentage: bool = True
    color_sequence: list[str] | None = None


class DonutChartData(PieChartData):
    """Data for donut chart."""

    hole_size: float = 0.4


class LineChartData(BaseModel):
    """Data for line chart."""

    title: str
    x_values: list[str]
    y_values: list[float]
    x_label: str = ""
    y_label: str = ""
    fill_area: bool = False
    show_markers: bool = True
    color: str | None = None


class HistogramData(BaseModel):
    """Data for histogram."""

    title: str
    bins: list[str]
    counts: list[int]
    x_label: str = ""
    y_label: str = ""
    color: str | None = None
