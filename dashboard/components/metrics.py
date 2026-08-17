"""Professional metric card components with modern design."""

from typing import Optional
from dataclasses import dataclass

import streamlit as st

from components.icons import get_icon
from core.theme import COLORS


@dataclass
class MetricCardData:
    """Data for a metric card."""

    title: str
    value: str | int | float
    icon: Optional[str] = None
    color: Optional[str] = None
    subtitle: Optional[str] = None
    trend: Optional[float] = None
    trend_label: Optional[str] = None


def render_metric_card(data: MetricCardData) -> None:
    """
    Render a professional metric card using Streamlit components.
    
    Args:
        data: MetricCardData with title, value, icon, color, etc.
    """
    color = data.color or COLORS["accent"]
    
    # Use Streamlit columns and metrics for clean rendering
    with st.container():
        # Card container with styling
        st.markdown(
            f"""
        <style>
            .metric-card-container {{
                background: {COLORS['card_bg']};
                border-radius: 16px;
                padding: 1.25rem 1.5rem;
                border: 1px solid {COLORS['border']};
                box-shadow: 0 1px 3px rgba(0,0,0,0.04);
                transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                height: 100%;
                min-height: 120px;
            }}
            .metric-card-container:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 40px rgba(0,0,0,0.06);
                border-color: {color}40;
            }}
            .metric-card-icon {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 40px;
                height: 40px;
                border-radius: 12px;
                background: {color}12;
                margin-bottom: 0.5rem;
            }}
            .metric-card-value {{
                font-size: 1.75rem;
                font-weight: 700;
                color: {COLORS['primary']};
                letter-spacing: -0.02em;
                line-height: 1.2;
            }}
            .metric-card-title {{
                font-size: 0.7rem;
                font-weight: 500;
                color: {COLORS['text_light']};
                text-transform: uppercase;
                letter-spacing: 0.06em;
                margin-top: 0.15rem;
            }}
            .metric-card-subtitle {{
                font-size: 0.65rem;
                color: {COLORS['text_lighter']};
                margin-top: 0.25rem;
            }}
            .metric-card-trend {{
                font-size: 0.7rem;
                font-weight: 600;
                margin-top: 0.25rem;
            }}
        </style>
        """,
            unsafe_allow_html=True,
        )
        
        # Get icon
        icon_name = data.icon or "jobs_metric"
        icon_svg = get_icon(icon_name, size=20, color=color)
        
        # Build card HTML
        trend_html = ""
        if data.trend is not None:
            trend_color = COLORS["success"] if data.trend > 0 else COLORS["highlight"]
            trend_icon = "↑" if data.trend > 0 else "↓"
            trend_html = f"""
            <div class="metric-card-trend" style="color:{trend_color};">
                {trend_icon} {abs(data.trend):.1f}%
                {f'<span style="color:{COLORS["text_light"]};font-weight:400;">{data.trend_label}</span>' if data.trend_label else ''}
            </div>
            """
        
        subtitle_html = f'<div class="metric-card-subtitle">{data.subtitle}</div>' if data.subtitle else ""
        
        st.markdown(
            f"""
        <div class="metric-card-container">
            <div class="metric-card-icon">{icon_svg}</div>
            <div class="metric-card-value">{data.value}</div>
            <div class="metric-card-title">{data.title}</div>
            {trend_html}
            {subtitle_html}
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_metric_row(metrics: list[MetricCardData], columns: int = 4) -> None:
    """Render a row of professional metric cards."""
    if not metrics:
        st.info("No metrics to display")
        return

    cols = st.columns(min(columns, len(metrics)))
    for i, metric in enumerate(metrics):
        with cols[i % len(cols)]:
            render_metric_card(metric)