# dashboard/components/loading.py
"""Loading state components with improved UX."""

from contextlib import contextmanager

import streamlit as st


@contextmanager
def loading_spinner(text: str = "Loading..."):
    """Context manager for loading states with better UX."""
    with st.spinner(text):
        yield


def show_loading_card(text: str = "Loading data...", icon: str = "⏳"):
    """Show a loading card with icon."""
    return st.info(f"{icon} {text}")


def show_skeleton_loader(rows: int = 3, height: int = 60):
    """Show skeleton loader for tables with shimmer animation."""
    # Add CSS for shimmer animation - escape curly braces with double braces
    st.markdown(
        f"""
    <style>
        @keyframes shimmer {{
            0% {{ background-position: -200% 0; }}
            100% {{ background-position: 200% 0; }}
        }}
        .skeleton-row {{
            height: {height}px;
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: 8px;
            margin: 6px 0;
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    for _ in range(rows):
        st.markdown('<div class="skeleton-row"></div>', unsafe_allow_html=True)


def show_loading_animation(message: str = "Loading...", icon: str = "🔄"):
    """Show loading animation with spinning icon."""
    return st.markdown(
        f"""
    <div style="display: flex; align-items: center; gap: 1rem; padding: 1rem;">
        <div style="
            width: 24px;
            height: 24px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #0f3460;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        "></div>
        <span style="color: #636e72;">{icon} {message}</span>
        <style>
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </div>
    """,
        unsafe_allow_html=True,
    )
