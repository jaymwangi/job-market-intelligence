# dashboard/components/metrics.py
"""Reusable metric card components."""
import streamlit as st
from typing import Optional, Dict, Any
from dashboard.schemas.chart_data import MetricCardData


def create_metric_card(data: MetricCardData) -> Dict[str, Any]:
    """
    Create a professional metric card.
    
    Args:
        data: MetricCardData with title, value, icon, color, etc.
    
    Returns:
        Dictionary with HTML content for rendering
    """
    # Professional color palette
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
    
    # Determine color based on metric type if not specified
    color = data.color or colors.get("accent", "#0f3460")
    
    # Format change indicator
    change_html = ""
    if data.change is not None:
        change_color = "#00b894" if data.change_direction == "up" else "#e94560" if data.change_direction == "down" else colors["text_light"]
        change_icon = "↑" if data.change_direction == "up" else "↓" if data.change_direction == "down" else ""
        change_html = f"""
        <div style="
            margin-top: 8px;
            color: {change_color};
            font-size: 0.85rem;
            font-weight: 500;
        ">
            {change_icon} {data.change:+.1f}%
        </div>
        """
    
    html = f"""
    <div style="
        background: {colors['card_bg']};
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        border: 1px solid {colors['border']};
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
        height: 100%;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    ">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div style="
                    color: {colors['text_light']};
                    font-size: 0.8rem;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                    margin-bottom: 4px;
                ">
                    {data.title}
                </div>
                <div style="
                    font-size: 1.75rem;
                    font-weight: 700;
                    color: {colors['primary']};
                    line-height: 1.2;
                ">
                    {data.value}
                </div>
                {change_html}
            </div>
            <div style="
                font-size: 1.5rem;
                opacity: 0.8;
                background: {color}10;
                padding: 8px;
                border-radius: 8px;
                line-height: 1;
            ">
                {data.icon or "📊"}
            </div>
        </div>
        {f'<div style="color: {colors["text_light"]}; font-size: 0.75rem; margin-top: 4px;">{data.subtitle}</div>' if data.subtitle else ''}
    </div>
    """
    
    return {"html": html}


def render_metric_card(data: MetricCardData) -> None:
    """Render a metric card directly in Streamlit."""
    card = create_metric_card(data)
    st.markdown(card['html'], unsafe_allow_html=True)


def render_metric_row(metrics: list[MetricCardData], columns: int = 4) -> None:
    """Render a row of metric cards."""
    cols = st.columns(columns)
    for i, metric in enumerate(metrics):
        with cols[i % columns]:
            render_metric_card(metric)