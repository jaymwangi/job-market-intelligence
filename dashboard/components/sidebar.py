import streamlit as st

from core.config import settings
from utils.state import StateManager

def render_sidebar():
    """Render the sidebar navigation."""
    with st.sidebar:
        st.title(f"{settings.APP_ICON} {settings.APP_TITLE}")
        st.markdown("---")
        
        # Navigation buttons
        pages = {
            "📊 Overview": "overview",
            "💼 Jobs": "jobs",
            "📈 Analytics": "analytics",
            "ℹ️ About": "about",
        }
        
        for label, page_id in pages.items():
            if st.button(label, use_container_width=True):
                StateManager.set_current_page(page_id)
                st.rerun()
        
        st.markdown("---")
        st.caption("Sprint 5.1 • Foundation")