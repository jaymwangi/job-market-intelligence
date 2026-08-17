"""Professional SVG icon system with rendering helpers."""

import streamlit as st
from typing import Optional

# Color constants for consistent theming
class IconColor:
    PRIMARY = "#6366f1"      # Indigo
    SUCCESS = "#10b981"      # Emerald
    WARNING = "#f59e0b"      # Amber
    DANGER = "#ef4444"       # Red
    INFO = "#3b82f6"         # Blue
    GRAY = "#6b7280"         # Gray
    DARK = "#1f2937"         # Dark


# Base icon definitions - using multiline strings properly
ICONS = {
    # Status
    "success": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        "label": "Success",
    },
    "error": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        "label": "Error",
    },
    "warning": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
        "label": "Warning",
    },
    "info": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        "label": "Info",
    },
    
    # Job listing icons
    "company": {
        "svg": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="15" y2="16"/></svg>',
        "label": "Company",
    },
    "location_pin": {
        "svg": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
        "label": "Location",
    },
    "calendar": {
        "svg": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
        "label": "Calendar",
    },
    "salary": {
        "svg": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="6" x2="12" y2="12"/><line x1="12" y1="12" x2="9" y2="15"/><line x1="12" y1="12" x2="15" y2="15"/></svg>',
        "label": "Salary",
    },
    
    # Navigation
    "overview": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
        "label": "Overview",
    },
    "jobs": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
        "label": "Jobs",
    },
    "analytics": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12v-2a5 5 0 0 0-5-5H8a5 5 0 0 0-5 5v2"/><circle cx="12" cy="16" r="5"/><path d="M12 11v5"/><path d="M9 16h6"/></svg>',
        "label": "Analytics",
    },
    "about": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        "label": "About",
    },
    
    # Metrics
    "jobs_metric": {
        "svg": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20V14"/><rect x="2" y="2" width="20" height="20" rx="2"/></svg>',
        "label": "Jobs",
    },
    "companies_metric": {
        "svg": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="15" y2="16"/></svg>',
        "label": "Companies",
    },
    "skills_metric": {
        "svg": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
        "label": "Skills",
    },
    "salary_metric": {
        "svg": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="6" x2="12" y2="12"/><line x1="12" y1="12" x2="9" y2="15"/><line x1="12" y1="12" x2="15" y2="15"/></svg>',
        "label": "Salary",
    },
    
    # Charts / Analytics
    "location": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
        "label": "Location",
    },
    "trends": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l6-6 4 4 8-8"/><path d="M21 7v8"/><path d="M21 7h-8"/></svg>',
        "label": "Trends",
    },
    "employment": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
        "label": "Employment",
    },
    
    # Actions
    "refresh": {
        "svg": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>',
        "label": "Refresh",
    },
    
    # Tech & Scoring icons (replacing emojis)
    "tech": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 6L2 12L8 18"/><path d="M16 6L22 12L16 18"/><path d="M14 4L10 20"/></svg>',
        "label": "Tech",
    },
    "score": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
        "label": "Score",
    },
    "filter": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 21V14"/><path d="M4 10V3"/><path d="M12 21V12"/><path d="M12 8V3"/><path d="M20 21V16"/><path d="M20 12V3"/><circle cx="4" cy="12" r="2"/><circle cx="12" cy="10" r="2"/><circle cx="20" cy="14" r="2"/></svg>',
        "label": "Filter",
    },
    "download": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V15"/><path d="M7 10L12 15L17 10"/><path d="M12 15V3"/></svg>',
        "label": "Download",
    },
    "translate": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 7H3"/><path d="M5.5 7V13.5"/><path d="M13 7H18"/><path d="M15.5 7V13.5"/><path d="M20 7V13.5"/><path d="M10 13.5H20"/><path d="M12 17L8 21L4 17"/><path d="M21 17L19 21L17 17"/></svg>',
        "label": "Translate",
    },
    "briefcase": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 7H4C2.89543 7 2 7.89543 2 9V19C2 20.1046 2.89543 21 4 21H20C21.1046 21 22 20.1046 22 19V9C22 7.89543 21.1046 7 20 7Z"/><path d="M16 21V5C16 3.89543 15.1046 3 14 3H10C8.89543 3 8 3.89543 8 5V21"/></svg>',
        "label": "Briefcase",
    },
    "clock": {
        "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        "label": "Clock",
    },
}


def get_icon(name: str, size: int = 20, color: str = "currentColor") -> str:
    """Get SVG icon HTML with specified size and color."""
    icon = ICONS.get(name)
    if not icon:
        return ""

    svg = icon["svg"]
    # Replace size and color
    svg = svg.replace('width="20"', f'width="{size}"')
    svg = svg.replace('height="20"', f'height="{size}"')
    svg = svg.replace('stroke="currentColor"', f'stroke="{color}"')

    return svg


def render_icon(name: str, size: int = 20, color: str = "currentColor") -> None:
    """Render an SVG icon directly in Streamlit using markdown."""
    svg = get_icon(name, size, color)
    if svg:
        st.markdown(
            f'<span style="display:inline-flex;align-items:center;justify-content:center;">{svg}</span>',
            unsafe_allow_html=True,
        )


def icon_html(name: str, size: int = 20, color: str = "currentColor") -> str:
    """Get HTML-ready icon string for use in other HTML."""
    svg = get_icon(name, size, color)
    if not svg:
        return ""
    return f'<span style="display:inline-flex;align-items:center;justify-content:center;">{svg}</span>'


def icon_with_text(name: str, text: str, size: int = 16, 
                   color: str = "currentColor", gap: str = "6px") -> str:
    """Get HTML for icon with text next to it."""
    icon_svg = get_icon(name, size, color)
    if not icon_svg:
        return text
    return f'<span style="display:inline-flex;align-items:center;gap:{gap};">{icon_svg}<span>{text}</span></span>'


def metric_icon(name: str, size: int = 28, color: str = IconColor.PRIMARY) -> str:
    """Get HTML for metric card icon with background."""
    icon_svg = get_icon(name, size, color)
    if not icon_svg:
        return ""
    return f'<div style="background:{color}15;border-radius:10px;padding:0.75rem;display:flex;align-items:center;justify-content:center;width:{size+24}px;height:{size+24}px;">{icon_svg}</div>'


# Convenience functions for common icons
def job_icon(size: int = 20, color: str = "currentColor") -> str:
    """Get job/briefcase icon."""
    return get_icon("briefcase", size, color)


def tech_icon(size: int = 20, color: str = "currentColor") -> str:
    """Get technology icon."""
    return get_icon("tech", size, color)


def score_icon(size: int = 20, color: str = "currentColor") -> str:
    """Get score/star icon."""
    return get_icon("score", size, color)


def location_icon(size: int = 20, color: str = "currentColor") -> str:
    """Get location pin icon."""
    return get_icon("location_pin", size, color)


def time_icon(size: int = 20, color: str = "currentColor") -> str:
    """Get clock icon."""
    return get_icon("clock", size, color)


def company_icon(size: int = 20, color: str = "currentColor") -> str:
    """Get company icon."""
    return get_icon("company", size, color)


def filter_icon(size: int = 20, color: str = "currentColor") -> str:
    """Get filter icon."""
    return get_icon("filter", size, color)


def translate_icon(size: int = 20, color: str = "currentColor") -> str:
    """Get translate icon."""
    return get_icon("translate", size, color)


def refresh_icon(size: int = 20, color: str = "currentColor") -> str:
    """Get refresh icon."""
    return get_icon("refresh", size, color)


def salary_icon(size: int = 20, color: str = "currentColor") -> str:
    """Get salary icon."""
    return get_icon("salary", size, color)


def icon_button(text: str, icon_name: str, key: Optional[str] = None, 
                color: str = IconColor.PRIMARY, size: int = 16,
                use_container_width: bool = False) -> bool:
    """
    Create a button with an SVG icon inside it.
    
    Args:
        text: Button text
        icon_name: Name of the icon from ICONS dictionary
        key: Optional unique key for the button
        color: Color of the icon
        size: Size of the icon in pixels
        use_container_width: Whether to use full container width
        
    Returns:
        bool: True if button was clicked
    """
    icon_svg = get_icon(icon_name, size, color)
    
    # Use a container with flex to position icon and button
    container = st.container()
    with container:
        cols = st.columns([1, 4], gap="small")
        with cols[0]:
            st.markdown(
                f'<div style="display:flex;align-items:center;justify-content:center;height:38px;margin-top:2px;">{icon_svg}</div>',
                unsafe_allow_html=True
            )
        with cols[1]:
            # Only pass key if it's provided
            if key is not None:
                clicked = st.button(text, key=key, use_container_width=use_container_width)
            else:
                clicked = st.button(text, use_container_width=use_container_width)
    
    return clicked