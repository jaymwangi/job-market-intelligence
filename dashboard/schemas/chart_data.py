# dashboard/schemas/chart_data.py
"""Chart models for presentation layer."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class ChartType(str, Enum):
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
    change: Optional[float] = None
    change_direction: Optional[str] = None  # "up" or "down"
    icon: Optional[str] = None
    color: Optional[str] = None
    subtitle: Optional[str] = None


class BarChartData(BaseModel):
    """Data for bar chart."""

    title: str
    x_values: List[str]
    y_values: List[float]
    x_label: str = ""
    y_label: str = ""
    color: Optional[str] = None
    show_values: bool = False
    sort_by: Optional[str] = None  # "value" or "label"
    sort_descending: bool = True


class HorizontalBarChartData(BarChartData):
    """Data for horizontal bar chart."""

    pass


class PieChartData(BaseModel):
    """Data for pie/donut chart."""

    title: str
    labels: List[str]
    values: List[float]
    show_percentage: bool = True
    color_sequence: Optional[List[str]] = None


class DonutChartData(PieChartData):
    """Data for donut chart."""

    hole_size: float = 0.4


class LineChartData(BaseModel):
    """Data for line chart."""

    title: str
    x_values: List[str]
    y_values: List[float]
    x_label: str = ""
    y_label: str = ""
    fill_area: bool = False
    show_markers: bool = True
    color: Optional[str] = None


class HistogramData(BaseModel):
    """Data for histogram."""

    title: str
    bins: List[str]
    counts: List[int]
    x_label: str = ""
    y_label: str = ""
    color: Optional[str] = None
