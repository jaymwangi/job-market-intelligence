# dashboard/components/metrics.py
"""Professional metric card components with modern design."""

from typing import Any, Dict, List

import streamlit as st

from dashboard.schemas.chart_data import MetricCardData
from dashboard.components.icons import get_icon


def create_metric_card(data: MetricCardData) -> Dict[str, Any]:
    """
    Create a professional metric card.

    Args:
        data: MetricCardData with title, value, icon, color, etc.

    Returns:
        Dictionary with HTML content for rendering
    """
    colors = {
        "primary": "#1a1a2e",
        "secondary": "#16213e",
        "accent": "#0f3460",
        "highlight": "#e94560",
        "success": "#00b894",
        "warning": "#fdcb6e",
        "info": "#0984e3",
        "background": "#f8f9fa",
        "card_bg": "#ffffff",
        "text": "#2d3436",
        "text_light": "#636e72",
        "border": "#e9ecef",
    }

    color = data.color or colors.get("accent", "#0f3460")

    # Map emoji to icon name
    icon_map = {
        "📊": "jobs_metric",
        "🏢": "companies_metric",
        "🎯": "skills_metric",
        "💰": "salary_metric",
        "📍": "location",
    }
    
    icon_name = icon_map.get(data.icon, "jobs_metric") if data.icon else "jobs_metric"
    icon_svg = get_icon(icon_name, size=22, color=color)

    change_html = ""
    if data.change is not None:
        change_color = (
            "#00b894"
            if data.change_direction == "up"
            else "#e94560" if data.change_direction == "down" else colors["text_light"]
        )
        change_icon = (
            "↑"
            if data.change_direction == "up"
            else "↓" if data.change_direction == "down" else ""
        )
        change_html = f'<div style="margin-top:6px;color:{change_color};font-size:0.75rem;font-weight:500;display:flex;align-items:center;gap:2px;">{change_icon} {data.change:+.1f}%</div>'

    subtitle_html = (
        f'<div style="color:{colors["text_light"]};font-size:0.65rem;margin-top:6px;font-weight:400;letter-spacing:0.02em;">{data.subtitle}</div>'
        if data.subtitle
        else ""
    )

    html = (
        f'<div style="background:{colors["card_bg"]};border-radius:12px;padding:1.25rem 1.5rem;border:1px solid {colors["border"]};box-shadow:0 1px 3px rgba(0,0,0,0.04);height:100%;min-height:110px;display:flex;flex-direction:column;justify-content:space-between;transition:all 0.2s ease;">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
        f'<div style="flex:1;">'
        f'<div style="color:{colors["text_light"]};font-size:0.65rem;font-weight:500;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">{data.title}</div>'
        f'<div style="font-size:1.75rem;font-weight:700;color:{colors["primary"]};line-height:1.2;letter-spacing:-0.02em;">{data.value}</div>'
        f'{change_html}'
        f'</div>'
        f'<div style="width:36px;height:36px;display:flex;align-items:center;justify-content:center;background:{color}08;border-radius:10px;margin-left:12px;flex-shrink:0;">'
        f'{icon_svg}'
        f'</div>'
        f'</div>'
        f'{subtitle_html}'
        f'</div>'
    )

    return {"html": html}


def render_metric_card(data: MetricCardData) -> None:
    """Render a professional metric card directly in Streamlit."""
    card = create_metric_card(data)
    st.markdown(card["html"], unsafe_allow_html=True)


def render_metric_row(metrics: List[MetricCardData], columns: int = 4) -> None:
    """Render a row of professional metric cards."""
    if not metrics:
        st.info("No metrics to display")
        return

    cols = st.columns(min(columns, len(metrics)))
    for i, metric in enumerate(metrics):
        with cols[i % len(cols)]:
            render_metric_card(metric)