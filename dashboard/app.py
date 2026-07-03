import streamlit as st
import sys
import os

# Add the dashboard directory to the path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import settings
from utils.state import StateManager
from components.sidebar import render_sidebar

# Page configuration
st.set_page_config(
    page_title=settings.APP_TITLE,
    page_icon=settings.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
StateManager.init()

# Render sidebar
render_sidebar()

# Render selected page
page = StateManager.get_current_page()

if page == "overview":
    from pages.overview import render
elif page == "jobs":
    from pages.jobs import render
elif page == "analytics":
    from pages.analytics import render
elif page == "about":
    from pages.about import render
else:
    st.error(f"Page '{page}' not found")
    render = None

if render:
    render()

# Footer
st.markdown("---")
st.caption(f"© 2024 {settings.APP_TITLE} • Sprint 5.1")