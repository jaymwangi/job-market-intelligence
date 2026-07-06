# dashboard/components/layout.py
"""Reusable layout components with SVG icons."""

from datetime import datetime
from typing import List, Optional

import streamlit as st

from dashboard.components.icons import get_icon

# Consistent spacing constants
SPACING = {
    "section": "1.5rem",
    "subsection": "1rem",
    "card": "1.25rem",
    "element": "0.5rem",
}


def page_header(
    title: str, subtitle: Optional[str] = None, icon: Optional[str] = None
) -> None:
    """
    Render a professional page header with SVG icon.

    Args:
        title: Page title
        subtitle: Optional subtitle
        icon: Optional icon name (e.g., "analytics", "jobs", "about")
    """
    icon_svg = ""
    if icon:
        # Map emoji to icon name for backward compatibility
        icon_map = {
            "📊": "analytics",
            "💼": "jobs",
            "ℹ️": "about",
            "📈": "trends",
        }
        icon_name = icon_map.get(icon, icon)
        icon_svg = get_icon(icon_name, size=32, color="#1a1a2e")
        icon_html_content = f'<span style="display:inline-flex;margin-right:0.75rem;">{icon_svg}</span>'
    else:
        icon_html_content = ""

    st.markdown(
        f"""
    <div style="margin-bottom: {SPACING['section']};">
        <div style="display: flex; align-items: center;">
            {icon_html_content}
            <div>
                <div style="
                    font-size: 2rem;
                    font-weight: 700;
                    color: #1a1a2e;
                    letter-spacing: -0.02em;
                ">
                    {title}
                </div>
                {f'<div style="color: #636e72; font-size: 0.95rem; font-weight: 400; margin-top: 0.25rem;">{subtitle}</div>' if subtitle else ''}
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def section_header(
    title: str, subtitle: Optional[str] = None, icon: Optional[str] = None
) -> None:
    """
    Render a professional section header with SVG icon.

    Args:
        title: Section title
        subtitle: Optional subtitle
        icon: Optional icon name (e.g., "location", "skills_metric", "companies_metric")
    """
    icon_svg = ""
    if icon:
        # Map emoji to icon name for backward compatibility
        icon_map = {
            "📍": "location",
            "🎯": "skills_metric",
            "🏢": "companies_metric",
            "💰": "salary_metric",
            "💼": "employment",
            "📈": "trends",
            "📊": "analytics",
        }
        icon_name = icon_map.get(icon, icon)
        icon_svg = get_icon(icon_name, size=20, color="#1a1a2e")
        icon_html_content = f'<span style="display:inline-flex;margin-right:0.5rem;">{icon_svg}</span>'
    else:
        icon_html_content = ""

    st.markdown(
        f"""
    <div style="margin: {SPACING['section']} 0 {SPACING['subsection']} 0;">
        <div style="
            font-size: 1.25rem;
            font-weight: 600;
            color: #1a1a2e;
            display: flex;
            align-items: center;
        ">
            {icon_html_content}{title}
        </div>
        {f'<div style="color: #636e72; font-size: 0.9rem; margin-top: 0.25rem;">{subtitle}</div>' if subtitle else ''}
        <div style="
            border-bottom: 2px solid #f8f9fa;
            margin-top: 0.5rem;
            padding-bottom: 0.5rem;
        "></div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def stats_bar(stats: List[tuple]) -> None:
    """
    Render a professional stats bar.

    Args:
        stats: List of (label, value) tuples
    """
    html = f"""
    <div style="
        display: flex;
        gap: 2rem;
        padding: 0.75rem 1.25rem;
        background: #ffffff;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        margin: 0 0 {SPACING['section']} 0;
        flex-wrap: wrap;
    ">
    """

    for i, (label, value) in enumerate(stats):
        if i > 0:
            html += '<span style="color: #e9ecef; font-size: 1.25rem;">•</span>'
        html += f"""
        <div style="display: flex; align-items: baseline; gap: 0.5rem;">
            <span style="font-weight: 700; font-size: 1.1rem; color: #1a1a2e;">{value}</span>
            <span style="color: #636e72; font-size: 0.85rem;">{label}</span>
        </div>
        """

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def card(content: str, title: Optional[str] = None, icon: Optional[str] = None) -> None:
    """
    Render a consistent card.

    Args:
        content: HTML content for the card
        title: Optional card title
        icon: Optional icon name
    """
    icon_html_content = ""
    if icon:
        icon_svg = get_icon(icon, size=16, color="#1a1a2e")
        icon_html_content = f'<span style="display:inline-flex;margin-right:0.5rem;">{icon_svg}</span>'

    title_html = (
        f'<div style="font-weight: 600; font-size: 1rem; color: #1a1a2e; margin-bottom: 0.5rem; display:flex; align-items:center;">{icon_html_content} {title}</div>'
        if title
        else ""
    )

    st.markdown(
        f"""
    <div style="
        background: #ffffff;
        border-radius: 12px;
        padding: {SPACING['card']};
        border: 1px solid #e9ecef;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin: {SPACING['element']} 0;
    ">
        {title_html}
        <div>{content}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def divider() -> None:
    """Render a consistent divider."""
    st.markdown(
        """
    <hr style="
        border: none;
        height: 1px;
        background: #e9ecef;
        margin: 1.5rem 0;
    ">
    """,
        unsafe_allow_html=True,
    )


def info_bar(text: str, icon: str = "info") -> None:
    """Render a professional info bar with SVG icon."""
    icon_svg = get_icon(icon, size=16, color="#0f3460")
    st.markdown(
        f"""
    <div style="
        background: #f8f9fa;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 1rem 0;
        color: #636e72;
        font-size: 0.9rem;
        border-left: 3px solid #0f3460;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    ">
        <span style="display:inline-flex;">{icon_svg}</span>
        {text}
    </div>
    """,
        unsafe_allow_html=True,
    )


def timestamp() -> None:
    """Render current timestamp."""
    st.markdown(
        f"""
    <div style="
        color: #636e72;
        font-size: 0.8rem;
        font-weight: 400;
        text-align: right;
        padding: 0.25rem 0;
    ">
        Last updated: {datetime.now().strftime("%b %d, %Y at %I:%M %p")}
    </div>
    """,
        unsafe_allow_html=True,
    )


def refresh_button(label: str = "Refresh", key: str = "refresh_button") -> bool:
    """
    Render a professional refresh button with SVG icon.

    Returns:
        True if button was clicked
    """
    icon = get_icon("refresh", size=16, color="#ffffff")
    
    # Use a simple approach - the SVG renders in the button label
    return st.button(
        f"{icon} {label}",
        use_container_width=True,
        key=key,
        help="Refresh dashboard"
    )