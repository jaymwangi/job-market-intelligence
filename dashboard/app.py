import streamlit as st
import sys
import os

dashboard_dir = os.path.dirname(os.path.abspath(__file__))
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

from core.config import settings
from utils.state import StateManager
from components.sidebar import render_sidebar

st.set_page_config(
    page_title=settings.APP_TITLE,
    page_icon=settings.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

StateManager.init()
render_sidebar()

# Get navigation state
page = StateManager.get_current_page()

if page == "overview":
    from pages.overview import render
    render()
elif page == "jobs":
    from pages.jobs import render
    render()
elif page == "analytics":
    from pages.analytics import render
    render()
elif page == "about":
    from pages.about import render
    render()
else:
    st.error(f"Page '{page}' not found")

st.markdown("---")
st.caption(f"© 2024 {settings.APP_TITLE} • Sprint 5.2")