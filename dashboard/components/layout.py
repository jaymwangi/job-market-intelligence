# dashboard/components/layout.py
"""Reusable layout components."""
import streamlit as st
from typing import List, Optional, Callable, Any
from datetime import datetime


def section_header(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None) -> None:
    """
    Render a professional section header.
    
    Args:
        title: Section title
        subtitle: Optional subtitle
        icon: Optional emoji icon
    """
    icon_html = f'<span style="font-size: 1.2rem; margin-right: 0.5rem;">{icon}</span>' if icon else ''
    
    st.markdown(f"""
    <div style="margin: 1.5rem 0 0.5rem 0;">
        <div style="
            font-size: 1.25rem;
            font-weight: 600;
            color: #1a1a2e;
            display: flex;
            align-items: center;
        ">
            {icon_html}{title}
        </div>
        {f'<div style="color: #636e72; font-size: 0.9rem; margin-top: 0.25rem;">{subtitle}</div>' if subtitle else ''}
        <div style="
            border-bottom: 2px solid #f8f9fa;
            margin-top: 0.5rem;
            padding-bottom: 0.5rem;
        "></div>
    </div>
    """, unsafe_allow_html=True)


def info_bar(text: str, icon: str = "ℹ️") -> None:
    """Render a professional info bar."""
    st.markdown(f"""
    <div style="
        background: #f8f9fa;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 1rem 0;
        color: #636e72;
        font-size: 0.9rem;
        border-left: 3px solid #0f3460;
    ">
        {icon} {text}
    </div>
    """, unsafe_allow_html=True)


def stats_bar(stats: List[tuple]) -> None:
    """
    Render a professional stats bar.
    
    Args:
        stats: List of (label, value) tuples
    """
    html = '<div style="display: flex; gap: 2rem; padding: 0.75rem 1.25rem; background: #ffffff; border-radius: 10px; border: 1px solid #e9ecef; margin: 1rem 0 1.5rem 0; flex-wrap: wrap;">'
    
    for i, (label, value) in enumerate(stats):
        if i > 0:
            html += '<span style="color: #e9ecef; font-size: 1.25rem;">•</span>'
        html += f"""
        <div style="display: flex; align-items: baseline; gap: 0.5rem;">
            <span style="font-weight: 700; font-size: 1.1rem; color: #1a1a2e;">{value}</span>
            <span style="color: #636e72; font-size: 0.85rem;">{label}</span>
        </div>
        """
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def timestamp() -> None:
    """Render current timestamp."""
    st.markdown(f"""
    <div style="
        color: #636e72;
        font-size: 0.8rem;
        font-weight: 400;
        text-align: right;
        padding: 0.25rem 0;
    ">
        Last updated: {datetime.now().strftime("%b %d, %Y at %I:%M %p")}
    </div>
    """, unsafe_allow_html=True)


def refresh_button(label: str = "🔄 Refresh", key: str = "refresh_button") -> bool:
    """
    Render a professional refresh button.
    
    Returns:
        True if button was clicked
    """
    return st.button(label, use_container_width=True, key=key)


def page_header(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None) -> None:
    """
    Render a professional page header.
    
    Args:
        title: Page title
        subtitle: Optional subtitle
        icon: Optional emoji icon
    """
    icon_html = f'<span style="font-size: 2rem; margin-right: 0.75rem;">{icon}</span>' if icon else ''
    
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: center;">
            {icon_html}
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
    """, unsafe_allow_html=True)